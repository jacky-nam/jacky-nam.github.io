"""Draw the synthetic bench figures of the reference deck.

Every trace is generated from a formula and a fixed seed. No capture is read.
bench-conversion-result.png is the exception: it draws four measured summary numbers held in this file.
Run from any directory: python make_synthetic_figures.py
The clip needs an ffmpeg binary. The imageio-ffmpeg package supplies one.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import imageio_ffmpeg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation

DECK_DIR = Path(__file__).resolve().parent
IMAGE_DIR = DECK_DIR / "images"
MEDIA_DIR = DECK_DIR / "media"
RANDOM_SEED = 20261118
DPI = 200

COLOUR = {
    "ax": "#EE6677",
    "ay": "#228833",
    "az": "#4477AA",
    "gx": "#AA3377",
    "gy": "#DDAA33",
    "gz": "#009988",
    "pressure": "#EE7733",
    "reference": "#000000",
}

SAMPLE_RATE_HZ = 100.0
SAMPLE_PERIOD_S = 1.0 / SAMPLE_RATE_HZ
CAPTURE_DURATION_S = 300.0
SIMULATOR_BREATH_PERIOD_S = 5.0

AMBIENT_OXYGEN_PERCENT = 20.93
AMBIENT_CARBON_DIOXIDE_PERCENT = 0.04
RESPIRATORY_QUOTIENT = 0.85
GAS_LAG_S = 0.3

PEAK_FLOW_L_PER_MIN = 46.0
AMBIENT_PRESSURE_PA = 100470.0
PEAK_PRESSURE_SWING_PA = 150.0

COMPARISON_ERROR_LIMIT_PERCENT = 8.0

CLIP = {
    "start_s": 100.0,
    "duration_s": 30.0,
    "visible_window_s": 15.0,
    "frame_rate_hz": 20,
}

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.color": "#E6E6E6",
        "grid.linewidth": 0.6,
        "axes.edgecolor": "#BBBBBB",
        "animation.ffmpeg_path": imageio_ffmpeg.get_ffmpeg_exe(),
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.titlelocation": "left",
    }
)


def save(figure, file_name):
    figure.savefig(IMAGE_DIR / file_name, dpi=DPI, pil_kwargs={"quality": 90})
    plt.close(figure)
    print("(Status) --> wrote", file_name)


def allan_deviation_model(tau_s, white_noise, bias_floor, rng):
    # White noise falls as tau^-1/2; the root-sum-square with a constant floor bends the curve flat.
    clean = np.sqrt(white_noise**2 / tau_s + bias_floor**2)
    return clean * np.exp(rng.normal(0.0, 0.03, tau_s.size))


def draw_allan_deviation(rng):
    tau_s = np.logspace(-2, 2, 40)
    panels = [
        ("a1. Accelerometer, ax", "ax", 9.0e-4, 2.0e-4, "m/s²"),
        ("a2. Accelerometer, ay", "ay", 7.0e-4, 2.4e-4, "m/s²"),
        ("a3. Accelerometer, az", "az", 1.0e-3, 1.8e-4, "m/s²"),
        ("b1. Gyroscope, gx", "gx", 4.0e-3, 9.0e-4, "deg/s"),
        ("b2. Gyroscope, gy", "gy", 4.5e-3, 1.1e-3, "deg/s"),
        ("b3. Gyroscope, gz", "gz", 3.8e-3, 8.0e-4, "deg/s"),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(7.0, 3.69), constrained_layout=True)
    figure.suptitle("Synthetic data: Allan deviation at rest", fontsize=10)
    for axis, (title, key, white_noise, bias_floor, unit) in zip(axes.flat, panels):
        deviation = allan_deviation_model(tau_s, white_noise, bias_floor, rng)
        axis.loglog(tau_s, deviation, color=COLOUR[key], marker="o", markersize=2.2, linewidth=1.2)
        axis.axhline(bias_floor, color=COLOUR["reference"], linestyle=":", linewidth=0.9)
        axis.set_title(title)
        axis.set_xlabel("averaging time τ (s)")
        axis.set_ylabel(f"Allan deviation ({unit})")
    save(figure, "bench-allan-deviation.png")


def breath_starts_and_periods(rng, first_breath_s, end_s, random_pattern):
    starts_s = []
    periods_s = []
    depths = []
    start_s = first_breath_s
    while start_s < end_s:
        period_s = float(np.clip(rng.normal(4.6, 0.8), 3.0, 7.0)) if random_pattern else SIMULATOR_BREATH_PERIOD_S
        depth = float(np.clip(rng.normal(1.0, 0.22), 0.5, 1.6)) if random_pattern else 1.0
        starts_s.append(start_s)
        periods_s.append(period_s)
        depths.append(depth)
        start_s += period_s
    return starts_s, periods_s, depths


def breathing(time_s, rng, first_breath_s, random_pattern):
    """Return flow and the fraction of exhaled gas at the sensor, both on time_s."""
    flow_l_per_min = np.zeros_like(time_s)
    exhaled_fraction = np.zeros_like(time_s)
    starts_s, periods_s, depths = breath_starts_and_periods(rng, first_breath_s, time_s[-1], random_pattern)
    for start_s, period_s, depth in zip(starts_s, periods_s, depths):
        inhale_s = 0.32 * period_s
        exhale_s = 0.40 * period_s
        phase_s = time_s - start_s
        in_inhale = (phase_s >= 0.0) & (phase_s < inhale_s)
        in_exhale = (phase_s >= inhale_s) & (phase_s < inhale_s + exhale_s)
        in_breath_out = (phase_s >= inhale_s) & (phase_s < period_s)
        exhale_phase_s = phase_s - inhale_s

        flow_l_per_min[in_inhale] = depth * PEAK_FLOW_L_PER_MIN * np.sin(np.pi * phase_s[in_inhale] / inhale_s)
        # The inhale area is depth * peak * 2 * inhale_s / pi. The scale below gives the exhale the same area.
        exhale_shape = np.sin(np.pi * exhale_phase_s[in_exhale] / exhale_s) ** 0.6 * np.exp(-exhale_phase_s[in_exhale] / (0.45 * exhale_s))
        inhale_area = depth * PEAK_FLOW_L_PER_MIN * 2.0 * inhale_s / np.pi
        flow_l_per_min[in_exhale] = -exhale_shape * inhale_area / (exhale_shape.sum() * SAMPLE_PERIOD_S)

        exhaled_fraction[in_breath_out] = depth**0.3 * (1.0 - np.exp(-exhale_phase_s[in_breath_out] / (0.25 * exhale_s)))
    return flow_l_per_min, exhaled_fraction


def first_order_lag(signal, time_constant_s):
    smoothing = SAMPLE_PERIOD_S / (time_constant_s + SAMPLE_PERIOD_S)
    lagged = np.empty_like(signal)
    lagged[0] = signal[0]
    for index in range(1, signal.size):
        lagged[index] = lagged[index - 1] + smoothing * (signal[index] - lagged[index - 1])
    return lagged


def synthetic_record(rng, duration_s, first_breath_s, random_pattern, gain_error_percent=0.0):
    """Return one record. A gain error scales flow, so volume and pressure follow it."""
    time_s = np.arange(0.0, duration_s, SAMPLE_PERIOD_S)
    ideal_flow_l_per_min, exhaled_fraction = breathing(time_s, rng, first_breath_s, random_pattern)
    flow_l_per_min = ideal_flow_l_per_min * (1.0 + gain_error_percent / 100.0)
    # L/min to L/s is /60; the running sum times the sample period is the integral.
    volume_l = np.cumsum(flow_l_per_min) / 60.0 * SAMPLE_PERIOD_S

    pressure_swing_pa = PEAK_PRESSURE_SWING_PA * flow_l_per_min / PEAK_FLOW_L_PER_MIN
    absolute_pressure_pa = AMBIENT_PRESSURE_PA + pressure_swing_pa + rng.normal(0.0, 1.5, time_s.size)

    end_tidal_carbon_dioxide_percent = 4.6
    carbon_dioxide_percent = AMBIENT_CARBON_DIOXIDE_PERCENT + end_tidal_carbon_dioxide_percent * first_order_lag(exhaled_fraction, GAS_LAG_S)
    # Each 1 % of CO2 produced uses 1 / RQ % of O2.
    oxygen_percent = AMBIENT_OXYGEN_PERCENT - (carbon_dioxide_percent - AMBIENT_CARBON_DIOXIDE_PERCENT) / RESPIRATORY_QUOTIENT
    carbon_dioxide_percent = carbon_dioxide_percent + rng.normal(0.0, 0.02, time_s.size)
    oxygen_percent = oxygen_percent + rng.normal(0.0, 0.02, time_s.size)

    breath_motion = np.abs(flow_l_per_min) / PEAK_FLOW_L_PER_MIN
    acceleration_m_per_s2 = 9.81 + 0.03 * breath_motion * rng.normal(0.0, 1.0, time_s.size) + rng.normal(0.0, 0.012, time_s.size)
    angular_rate_deg_per_s = np.abs(0.10 + 0.25 * breath_motion + rng.normal(0.0, 0.03, time_s.size))

    return {
        "time_s": time_s,
        "flow_l_per_min": flow_l_per_min,
        "volume_l": volume_l,
        "absolute_pressure_pa": absolute_pressure_pa,
        "oxygen_percent": oxygen_percent,
        "carbon_dioxide_percent": carbon_dioxide_percent,
        "acceleration_m_per_s2": acceleration_m_per_s2,
        "angular_rate_deg_per_s": angular_rate_deg_per_s,
    }


def plot_gas(axis, record, in_window):
    axis.plot(record["time_s"][in_window], record["oxygen_percent"][in_window], color=COLOUR["az"], linewidth=0.7)
    axis.set_ylabel("O₂ (%)", color=COLOUR["az"])
    gas_axis = axis.twinx()
    gas_axis.plot(record["time_s"][in_window], record["carbon_dioxide_percent"][in_window], color=COLOUR["ay"], linewidth=0.7)
    gas_axis.set_ylabel("CO₂ (%)", color=COLOUR["ay"])
    gas_axis.grid(False)


def draw_capture(record):
    time_s = record["time_s"]
    everything = np.ones(time_s.size, dtype=bool)
    figure, axes = plt.subplots(
        4, 1, figsize=(7.0, 4.45), sharex=True, constrained_layout=True,
        gridspec_kw={"height_ratios": [2, 2, 2, 3]},
    )
    figure.suptitle("Synthetic data: 300 s capture", fontsize=10)
    axes[0].plot(time_s, record["acceleration_m_per_s2"], color=COLOUR["az"], linewidth=0.6)
    axes[0].set_ylabel("|a| (m/s²)")
    axes[1].plot(time_s, record["angular_rate_deg_per_s"], color=COLOUR["gx"], linewidth=0.6)
    axes[1].set_ylabel("|ω| (deg/s)")
    axes[2].plot(time_s, record["absolute_pressure_pa"], color=COLOUR["pressure"], linewidth=0.6)
    axes[2].set_ylabel("absolute\npressure (Pa)")
    axes[2].ticklabel_format(useOffset=False)
    plot_gas(axes[3], record, everything)
    axes[3].set_xlabel("time (s)")
    axes[3].set_xlim(0.0, CAPTURE_DURATION_S)
    save(figure, "bench-capture-300s.png")


def draw_breath_gas(record):
    time_s = record["time_s"]
    in_window = (time_s >= 30.0) & (time_s < 90.0)
    figure, axes = plt.subplots(3, 1, figsize=(7.0, 5.36), sharex=True, constrained_layout=True)
    figure.suptitle("Synthetic data: flow, volume and breath gas", fontsize=10)
    axes[0].plot(time_s[in_window], record["flow_l_per_min"][in_window], color=COLOUR["az"], linewidth=0.9)
    axes[0].axhline(0.0, color=COLOUR["reference"], linestyle=":", linewidth=0.8)
    axes[0].set_title("a. Flow")
    axes[0].set_ylabel("flow (L/min)")
    axes[1].plot(time_s[in_window], record["volume_l"][in_window], color=COLOUR["az"], linewidth=0.9)
    axes[1].set_title("b. Net volume")
    axes[1].set_ylabel("net volume (L)")
    plot_gas(axes[2], record, in_window)
    axes[2].set_title("c. O₂ and CO₂")
    axes[2].set_xlabel("time (s)")
    axes[2].set_xlim(30.0, 90.0)
    save(figure, "bench-breath-gas.png")


def small_axes(row_count, height_ratios):
    figure, axes = plt.subplots(
        row_count, 1, figsize=(4.33, 2.05), sharex=True, constrained_layout=True,
        gridspec_kw={"height_ratios": height_ratios},
    )
    for axis in axes:
        axis.tick_params(labelsize=6)
    axes[-1].set_xlabel("time (s)", fontsize=6)
    return figure, axes


def draw_simulator_ideal(ideal, in_window):
    figure, axes = small_axes(2, [1, 1])
    axes[0].set_title("Synthetic data: ideal simulator output", fontsize=7)
    axes[0].plot(ideal["time_s"][in_window], ideal["flow_l_per_min"][in_window], color=COLOUR["reference"], linewidth=0.9)
    axes[0].set_ylabel("flow\n(L/min)", fontsize=6)
    axes[1].plot(ideal["time_s"][in_window], ideal["volume_l"][in_window], color=COLOUR["reference"], linewidth=0.9)
    axes[1].set_ylabel("net volume\n(L)", fontsize=6)
    save(figure, "bench-simulator-ideal.png")


def draw_simulator_generated(generated, in_window):
    figure, axes = small_axes(3, [3, 3, 2])
    axes[0].set_title("Synthetic data: generated record", fontsize=7)
    axes[0].plot(generated["time_s"][in_window], generated["flow_l_per_min"][in_window], color=COLOUR["az"], linewidth=0.9)
    axes[0].set_ylabel("flow\n(L/min)", fontsize=6)
    axes[1].plot(generated["time_s"][in_window], generated["volume_l"][in_window], color=COLOUR["az"], linewidth=0.9)
    axes[1].set_ylabel("net volume\n(L)", fontsize=6)
    axes[2].plot(generated["time_s"][in_window], generated["absolute_pressure_pa"][in_window], color=COLOUR["pressure"], linewidth=0.6)
    axes[2].set_ylabel("abs. pressure\n(Pa)", fontsize=6)
    axes[2].ticklabel_format(useOffset=False)
    save(figure, "bench-simulator-generated.png")


def draw_simulator_comparison(ideal, generated, in_window, gain_error_percent):
    figure, axes = plt.subplots(2, 1, figsize=(8.66, 2.6), sharex=True, constrained_layout=True)
    axes[0].set_title(f"Synthetic data: generated record against ideal output, gain error {gain_error_percent:+.1f} %", fontsize=8)
    for axis, key, label in ((axes[0], "flow_l_per_min", "flow (L/min)"), (axes[1], "volume_l", "net volume (L)")):
        axis.plot(generated["time_s"][in_window], generated[key][in_window], color=COLOUR["az"], linewidth=1.0, label="generated record")
        axis.plot(ideal["time_s"][in_window], ideal[key][in_window], color=COLOUR["reference"], linestyle="--", linewidth=0.9, label="ideal output")
        axis.set_ylabel(label, fontsize=7)
        axis.tick_params(labelsize=7)
    axes[0].legend(ncol=2, fontsize=6, frameon=False, loc="upper right")
    axes[1].set_xlabel("time (s)", fontsize=7)
    save(figure, "bench-simulator-comparison.png")


def write_clip(ideal, generated):
    figure, axes = plt.subplots(
        3, 1, figsize=(8.64, 4.08), sharex=True, constrained_layout=True,
        gridspec_kw={"height_ratios": [3, 3, 2]},
    )
    axes[0].set_title("Synthetic data: live plot of a generated record against ideal output")
    panels = (
        (axes[0], "flow_l_per_min", "flow (L/min)", COLOUR["az"], True),
        (axes[1], "volume_l", "net volume (L)", COLOUR["az"], True),
        (axes[2], "absolute_pressure_pa", "absolute\npressure (Pa)", COLOUR["pressure"], False),
    )
    in_clip = (generated["time_s"] >= CLIP["start_s"] - CLIP["visible_window_s"]) & (generated["time_s"] < CLIP["start_s"] + CLIP["duration_s"])
    lines = []
    for axis, key, label, colour, has_reference in panels:
        low = min(generated[key][in_clip].min(), ideal[key][in_clip].min())
        high = max(generated[key][in_clip].max(), ideal[key][in_clip].max())
        margin = 0.08 * (high - low)
        axis.set_ylim(low - margin, high + margin)
        axis.set_ylabel(label)
        axis.ticklabel_format(useOffset=False)
        generated_line, = axis.plot([], [], color=colour, linewidth=1.0, label="generated record")
        reference_line = None
        if has_reference:
            reference_line, = axis.plot([], [], color=COLOUR["reference"], linestyle="--", linewidth=0.9, label="ideal output")
        lines.append((key, generated_line, reference_line))
    axes[0].legend(ncol=2, fontsize=6, frameon=False, loc="upper right")
    axes[2].set_xlabel("time (s)")

    def draw_frame(frame_index):
        now_s = CLIP["start_s"] + frame_index / CLIP["frame_rate_hz"]
        visible = (generated["time_s"] >= now_s - CLIP["visible_window_s"]) & (generated["time_s"] <= now_s)
        for key, generated_line, reference_line in lines:
            generated_line.set_data(generated["time_s"][visible], generated[key][visible])
            if reference_line is not None:
                reference_line.set_data(ideal["time_s"][visible], ideal[key][visible])
        axes[2].set_xlim(now_s - CLIP["visible_window_s"], now_s)
        return []

    frame_count = int(CLIP["duration_s"] * CLIP["frame_rate_hz"])
    animation = FuncAnimation(figure, draw_frame, frames=frame_count, blit=False)
    MEDIA_DIR.mkdir(exist_ok=True)
    writer = FFMpegWriter(fps=CLIP["frame_rate_hz"], codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    animation.save(MEDIA_DIR / "simulator-capture.mp4", writer=writer, dpi=100)
    plt.close(figure)
    print("(Status) --> wrote", "simulator-capture.mp4")


MEASURED_CONVERSION_CHANGE = {
    "correlation": {"every third row": 0.7320, "every row": 0.7950},
    "noise_floor_pa": {"every third row": 0.376, "every row": 0.289},
}


def draw_conversion_result():
    """The only figure of measured values: two summary numbers at each conversion setting."""
    figure, axes = plt.subplots(1, 2, figsize=(8.66, 3.2), constrained_layout=True)
    panels = (
        (axes[0], "correlation", "a. Flow correlation with the simulator", "correlation r", "{:.2f}"),
        (axes[1], "noise_floor_pa", "b. Noise floor at zero flow", "standard deviation (Pa)", "{:.2f} Pa"),
    )
    for axis, key, title, label, value_format in panels:
        settings = list(MEASURED_CONVERSION_CHANGE[key])
        values = [MEASURED_CONVERSION_CHANGE[key][setting] for setting in settings]
        bars = axis.bar(settings, values, color=["#BBBBBB", COLOUR["az"]], width=0.55)
        axis.bar_label(bars, labels=[value_format.format(value) for value in values], fontsize=9, padding=3)
        change_percent = (values[1] / values[0] - 1.0) * 100.0
        axis.set_title(f"{title}: {change_percent:+.1f} %")
        axis.set_ylabel(label)
        axis.set_ylim(0.0, max(values) * 1.2)
        axis.grid(axis="x", visible=False)
    save(figure, "bench-conversion-result.png")


def main():
    rng = np.random.default_rng(RANDOM_SEED)
    draw_allan_deviation(rng)

    random_breaths = synthetic_record(rng, CAPTURE_DURATION_S, first_breath_s=8.0, random_pattern=True)
    draw_capture(random_breaths)
    draw_breath_gas(random_breaths)

    gain_error_percent = float(rng.uniform(-COMPARISON_ERROR_LIMIT_PERCENT, COMPARISON_ERROR_LIMIT_PERCENT))
    print("(Status) --> gain error percent", round(gain_error_percent, 1))
    ideal = synthetic_record(rng, CAPTURE_DURATION_S, first_breath_s=90.0, random_pattern=False)
    generated = synthetic_record(rng, CAPTURE_DURATION_S, first_breath_s=90.0, random_pattern=False, gain_error_percent=gain_error_percent)
    in_window = (ideal["time_s"] >= 85.0) & (ideal["time_s"] < 115.0)
    draw_simulator_ideal(ideal, in_window)
    draw_simulator_generated(generated, in_window)
    draw_simulator_comparison(ideal, generated, in_window, gain_error_percent)
    write_clip(ideal, generated)
    draw_conversion_result()


if __name__ == "__main__":
    main()
