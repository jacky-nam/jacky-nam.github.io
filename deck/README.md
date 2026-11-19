# Reference deck

Source for `ReferenceDeck.pdf` at the repo root. The deck is plain HTML/CSS
(`index.html`, `style.css`, `style-harvard.css`, figures under `images/`)
rendered to PDF with headless Chrome. `index.html` loads both stylesheets:
`style.css` is the base, `style-harvard.css` the checklist-layout theme on top.

## Synthetic figures

`make_synthetic_figures.py` draws the synthetic bench plots in `images/`
(`bench-*.png`, labelled "Synthetic data") and the 30 s demo clip written to
`media/simulator-capture.mp4` at the repo root. It needs `numpy`, `matplotlib`
and `imageio-ffmpeg`:

```sh
pip3 install numpy matplotlib imageio-ffmpeg
python3 deck/make_synthetic_figures.py
```

The Live demo link in `index.html` is the absolute
`https://jackynam.com/media/simulator-capture.mp4` so it works from the PDF.

## Re-render

After editing any deck source, rebuild the PDF with one command from the
repo root:

```sh
./deck/render.sh
```

(The script resolves its own location, so it also works run from any other
directory via its path.)

This renders `index.html` to a 16:9 landscape PDF and writes it to
`ReferenceDeck.pdf` at the repo root (the path the portfolio page embeds).

## Section dates

Each section divider slide carries a `Last Updated: <date>` line
(`<p class="updated">` in `index.html`). It is set by hand: when you change a
section, update the date on that section's divider and re-render.

## Requirements

- **Chrome or Chromium.** The script auto-detects Google Chrome / Chromium in
  `/Applications`, then falls back to a puppeteer-managed "Chrome for Testing"
  build (`npx puppeteer browsers install chrome`). Set `CHROME_BIN` to point at
  a specific binary:

  ```sh
  CHROME_BIN=/path/to/chrome ./deck/render.sh
  ```

- **PyMuPDF.** `set_metadata.py` (run automatically by `render.sh`) uses the
  `fitz` module to strip Chrome's default PDF metadata. Install it with:

  ```sh
  pip3 install pymupdf
  ```
