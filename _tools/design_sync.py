#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Copy the CSS, the component JS and the favicon from _design/site/assets/ to app/static/.

Run it with `mise run design-sync`. Never edit the copies in app/static/.
The prototype file splitwise-app.js is not copied: the app replaces it.
"""

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "_design" / "site" / "assets"
TARGET = REPO / "app" / "static"
FILES = {
    "splitwise.css": "css/splitwise.css",
    "splitwise.js": "js/splitwise.js",
    "favicon.svg": "favicon.svg",
}


def main() -> None:
    for name, dest in FILES.items():
        target = TARGET / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, target)
        print(f"copied {SOURCE.relative_to(REPO) / name} -> {target.relative_to(REPO)}")


if __name__ == "__main__":
    main()
