#!/usr/bin/env python3
"""Clear identifying document metadata on the rendered deck PDF.

Chrome's print-to-pdf writer stamps producer/creator fields by default.
This strips those and sets a plain title/no author so the shipped PDF
carries no trace of the tool that rendered it.
"""
import sys
import fitz


def main():
    src, dst = sys.argv[1], sys.argv[2]
    doc = fitz.open(src)
    doc.set_metadata({
        "title": "Reference Deck",
        "author": "",
        "subject": "",
        "keywords": "",
        "creator": "",
        "producer": "",
    })
    doc.save(dst, garbage=4, deflate=True)
    doc.close()


if __name__ == "__main__":
    main()
