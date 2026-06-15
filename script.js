/* Jacky Nam — portfolio interactions (minimal) */
(function () {
  "use strict";

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- reveal on scroll ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !prefersReduced) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e, i) => {
          if (e.isIntersecting) {
            e.target.style.transitionDelay = Math.min(i * 60, 180) + "ms";
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------- QRS complex (linked Q/R/S), morphing into EEG/EMG/EOG ---------- */
  const canvas = document.getElementById("signal");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d");
    const RATIO = 250 / 720; // height : width
    let w = 720, h = 250;

    function fit() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth || 720;
      h = w * RATIO;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    fit();

    const GREEN = "#79e2aa";

    // geometry — must match the .signal__label CSS positions
    const BASE = 0.66;  // baseline at 66% of canvas height (R up, Q/S dips below)
    const AMP  = 0.56;  // amplitude scale, fraction of canvas height
    const QX = 0.44, RX = 0.50, SX = 0.565; // Q / R / S positions along the width

    function gauss(x, c, sd) {
      const d = x - c;
      return Math.exp(-(d * d) / (2 * sd * sd));
    }

    // ECG — one static beat, P-QRS-T (matches the reference diagram), gentle breathing
    function ecg(xn, t) {
      const a = 1 + 0.04 * Math.sin(t * 1.6);
      return a * (
          0.08 * gauss(xn, 0.30, 0.030)   // P
        - 0.22 * gauss(xn, QX,   0.012)   // Q
        + 0.95 * gauss(xn, RX,   0.016)   // R
        - 0.30 * gauss(xn, SX,   0.014)   // S
        + 0.15 * gauss(xn, 0.72, 0.040)   // T
      );
    }

    // EEG — layered low-amplitude rhythms
    function eeg(xn, t) {
      return 0.14 * Math.sin(40 * xn + 3.1 * t)
           + 0.10 * Math.sin(73 * xn - 4.7 * t)
           + 0.06 * Math.sin(118 * xn + 6.3 * t)
           + 0.05 * Math.sin(31 * xn - 2.2 * t);
    }

    // EMG — high-frequency activity in contraction bursts
    function emg(xn, t) {
      const carrier = Math.sin(260 * xn + 9 * t) * Math.sin(151 * xn - 5 * t);
      let env = Math.max(0, Math.sin(6.283 * (xn * 1.5 - t * 0.18)));
      env *= env;
      return carrier * (0.07 + 0.45 * env);
    }

    // EOG — slow square-ish saccade deflections
    function eog(xn, t) {
      return 0.32 * Math.tanh(3.5 * Math.sin(6.283 * (xn * 0.9 - t * 0.07)))
           + 0.03 * Math.sin(45 * xn - 3 * t);
    }

    const SIGNALS = [ecg, eeg, emg, eog];
    const HOLD = 5.0; // ~seconds per signal before morphing to the next

    function sample(xn, t) {
      const phase = (t / HOLD) % SIGNALS.length;
      const idx = Math.floor(phase);
      let f = phase - idx;
      // hold each signal, morph during the last 30% of its window
      f = f < 0.7 ? 0 : (f - 0.7) / 0.3;
      f = f * f * (3 - 2 * f); // smoothstep
      const a = SIGNALS[idx](xn, t);
      const b = SIGNALS[(idx + 1) % SIGNALS.length](xn, t);
      return a * (1 - f) + b * f;
    }

    function drawTrace(t) {
      ctx.clearRect(0, 0, w, h);
      const yb = h * BASE;

      // dashed baseline, like the reference diagram
      ctx.save();
      ctx.strokeStyle = "rgba(121,226,170,0.22)";
      ctx.lineWidth = 1;
      ctx.setLineDash([6, 6]);
      ctx.beginPath(); ctx.moveTo(0, yb); ctx.lineTo(w, yb); ctx.stroke();
      ctx.restore();

      // trace
      ctx.strokeStyle = GREEN;
      ctx.lineWidth = 1.6;
      ctx.shadowBlur = 7;
      ctx.shadowColor = GREEN;
      ctx.beginPath();
      const N = 280;
      for (let i = 0; i <= N; i++) {
        const xn = i / N;
        const y = yb - sample(xn, t) * (h * AMP);
        i === 0 ? ctx.moveTo(xn * w, y) : ctx.lineTo(xn * w, y);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    let t = 0;
    let raf = null;

    function frame() {
      t += 0.025;
      drawTrace(t);
      raf = requestAnimationFrame(frame);
    }

    // repaint after layout changes (resize clears the canvas)
    window.addEventListener("resize", () => {
      fit();
      if (prefersReduced || !raf) drawTrace(0.4);
    });

    // safety net: if the canvas had no width at script time (fonts/layout late),
    // refit once everything has loaded
    window.addEventListener("load", () => {
      if (Math.abs((canvas.clientWidth || 720) - w) > 1) {
        fit();
        if (prefersReduced || !raf) drawTrace(0.4);
      }
    });

    if (prefersReduced) {
      drawTrace(0.4); // single static QRS frame
    } else {
      // animate only while visible
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting && !raf) raf = requestAnimationFrame(frame);
          else if (!e.isIntersecting && raf) { cancelAnimationFrame(raf); raf = null; }
        });
      }, { threshold: 0.05 });
      io.observe(canvas);
      drawTrace(0.4); // immediate first paint so the QRS is never blank
    }
  }
})();
