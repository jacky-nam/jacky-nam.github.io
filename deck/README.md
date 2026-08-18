# Reference deck

Source for `ReferenceDeck.pdf` at the repo root. The deck is plain HTML/CSS
(`index.html`, `style.css`, figures under `images/`) rendered to PDF with
headless Chrome.

## Re-render

After editing any deck source, rebuild the PDF with one command from anywhere
in the repo:

```sh
./deck/render.sh
```

This renders `index.html` to a 16:9 landscape PDF and writes it to
`ReferenceDeck.pdf` at the repo root (the path the portfolio page embeds).

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
