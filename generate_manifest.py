#!/usr/bin/env python3
"""
Scans a comic folder (one subfolder per chapter, images inside each) and
writes a manifest.json that the hosted SCROLL reader uses to build the
reading list — including each image's pixel dimensions, so the reader can
reserve the correct space for every page before it loads (no layout jump).

Works whether your chapter folders sit directly at the repo root, or are
tucked inside a wrapper folder (e.g. "Chapter Images/1/", "Chapter Images/2/",
...) to keep the repo listing clean — manifest.json is always written one
level up from whatever folder you point it at, so it ends up next to
index.html either way, and every path inside it is recorded relative to
THAT location (so the reader never needs to know about the wrapper folder).

Usage:
    pip install pillow

    # chapters directly at repo root:
    python3 generate_manifest.py /path/to/YourComic

    # chapters tucked inside a wrapper folder:
    python3 generate_manifest.py /path/to/YourComic/"Chapter Images"

Either way, this writes manifest.json into the PARENT of the folder you
pointed it at — i.e. next to index.html.
"""

import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("This script needs Pillow: pip install pillow")
    sys.exit(1)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def build_manifest(root: Path, path_prefix: str):
    chapters = []
    chapter_dirs = sorted(
        [d for d in root.iterdir() if d.is_dir()],
        key=lambda d: natural_key(d.name),
    )

    if not chapter_dirs:
        # No subfolders — treat the root itself as a single chapter.
        chapter_dirs = [root]

    for chapter_dir in chapter_dirs:
        images = sorted(
            [f for f in chapter_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS],
            key=lambda f: natural_key(f.name),
        )
        if not images:
            continue

        pages = []
        for img_path in images:
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
            except Exception as e:
                print(f"  ! skipping unreadable file {img_path.name}: {e}")
                continue

            rel = img_path.relative_to(root).as_posix()
            # Prefix so the path is correct relative to manifest.json's
            # location (one level up from `root`), not relative to `root`
            # itself.
            full_rel = f"{path_prefix}/{rel}" if path_prefix else rel
            pages.append({"file": full_rel, "w": w, "h": h})

        if pages:
            name = chapter_dir.name if chapter_dir != root else root.name
            chapters.append({"name": name, "pages": pages})
            print(f"  {name}: {len(pages)} pages")

    return {"chapters": chapters}


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 generate_manifest.py /path/to/ComicFolder')
        print('   or: python3 generate_manifest.py /path/to/ComicFolder/"Chapter Images"')
        sys.exit(1)

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a folder: {root}")
        sys.exit(1)

    # manifest.json always goes one level up from the scanned folder —
    # i.e. next to index.html — and paths are prefixed with the scanned
    # folder's own name so they still resolve correctly from there.
    out_dir = root.parent
    path_prefix = root.name

    print(f"Scanning {root} ...")
    manifest = build_manifest(root, path_prefix)

    total_pages = sum(len(c["pages"]) for c in manifest["chapters"])
    if not manifest["chapters"]:
        print("No images found. Check the folder structure.")
        sys.exit(1)

    out_path = out_dir / "manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"{len(manifest['chapters'])} chapters, {total_pages} pages total.")
    print(f'(paths inside manifest.json are prefixed with "{path_prefix}/")')
    print("\nNext: make sure index.html is in the same folder as manifest.json,")
    print("upload everything to your web host, and open index.html.")


if __name__ == "__main__":
    main()

