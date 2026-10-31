#!/usr/bin/env python3
"""Render index.html for a visual check.

  python3 scripts/screenshot.py [--out .preview]

Writes desktop-light, desktop-dark and mobile-light screenshots, each as a full page and as a
first screen ("-top"). Serves the folder on a temporary local port so fonts and images load the
way they do on GitHub Pages.

Needs Playwright: pip install playwright && python3 -m playwright install chromium
"""
from __future__ import annotations

import argparse
import http.server
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VIEWS = [
    # name, viewport, color scheme, device scale factor, mobile
    ("desktop-light", {"width": 1280, "height": 900}, "light", 1, False),
    ("desktop-dark", {"width": 1280, "height": 900}, "dark", 1, False),
    ("mobile-light", {"width": 390, "height": 844}, "light", 2, True),
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Screenshot the homepage in light, dark and mobile views.")
    ap.add_argument("--out", type=Path, default=ROOT / ".preview")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Run:\n"
              "  pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        return 3

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    args.out.mkdir(parents=True, exist_ok=True)

    written = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, viewport, scheme, scale, mobile in VIEWS:
            context = browser.new_context(viewport=viewport, color_scheme=scheme,
                                          device_scale_factor=scale, is_mobile=mobile)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
            page.goto(url, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            for suffix, full in (("", True), ("-top", False)):
                path = args.out / f"{name}{suffix}.png"
                page.screenshot(path=str(path), full_page=full)
                written.append(path)
            for e in errors:
                print(f"{name}: JavaScript error: {e}", file=sys.stderr)
            context.close()
        browser.close()
    server.shutdown()

    for path in written:
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
