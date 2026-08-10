#!/usr/bin/env python3
"""
Sorts loose page images like "seed Ch5.8.jpg" into numbered chapter
folders (5/, 6/, ...) matching whatever convention your existing folders
(1/, 2/, 3/, 4/) already use.

It only touches files sitting loose in the root folder — anything already
inside a subfolder is left alone.

Usage:
    # 1) Dry run first (default) — just prints what it WOULD do:
    python3 sort_into_chapters.py /path/to/YourComic

    # 2) Once the plan looks right, actually move the files:
    python3 sort_into_chapters.py /path/to/YourComic --apply

By default it looks for "Ch<number>" anywhere in the filename (case
insensitive) — matches "seed Ch5.8.jpg", "Ch12_003.png", "chapter5-01.jpg",
etc. If your filenames use a different pattern, edit CHAPTER_PATTERN below.
"""

import re
import shutil
import sys
from pathlib import Path

CHAPTER_PATTERN = re.compile(r"ch(?:apter)?[\s_\-]?(\d+)", re.IGNORECASE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}


def main():
    args = sys.argv[1:]
    apply_changes = "--apply" in args
    args = [a for a in args if a != "--apply"]

    if len(args) != 1:
        print("Usage: python3 sort_into_chapters.py /path/to/ComicFolder [--apply]")
        sys.exit(1)

    root = Path(args[0]).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a folder: {root}")
        sys.exit(1)

    loose_files = [
        f for f in root.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ]

    if not loose_files:
        print("No loose image files found in the root folder — nothing to sort.")
        return

    plan = {}   # chapter number (str) -> list of files
    unmatched = []

    for f in loose_files:
        m = CHAPTER_PATTERN.search(f.stem)
        if not m:
            unmatched.append(f)
            continue
        chapter_num = str(int(m.group(1)))  # normalizes "05" -> "5"
        plan.setdefault(chapter_num, []).append(f)

    print(f"Scanning {root}\n")

    if not plan:
        print("Couldn't match a chapter number in any filename.")
        print("Edit CHAPTER_PATTERN in this script to fit your naming, then rerun.")
        return

    for chapter_num in sorted(plan.keys(), key=int):
        files = sorted(plan[chapter_num], key=lambda f: f.name)
        dest = root / chapter_num
        exists_note = " (folder already exists)" if dest.exists() else " (will create)"
        print(f"Chapter {chapter_num}{exists_note}: {len(files)} files -> {dest.name}/")

    if unmatched:
        print(f"\n{len(unmatched)} file(s) didn't match a chapter number and will be left alone:")
        for f in unmatched[:10]:
            print(f"   {f.name}")
        if len(unmatched) > 10:
            print(f"   ... and {len(unmatched) - 10} more")

    if not apply_changes:
        print("\nDry run only — nothing was moved.")
        print("If this plan looks right, rerun with --apply to actually move the files:")
        print(f"    python3 sort_into_chapters.py \"{root}\" --apply")
        return

    print("\nMoving files...")
    for chapter_num, files in plan.items():
        dest = root / chapter_num
        dest.mkdir(exist_ok=True)
        for f in files:
            target = dest / f.name
            if target.exists():
                print(f"  ! skipping {f.name} — already exists in {dest.name}/")
                continue
            shutil.move(str(f), str(target))
    print("Done. Loose files have been moved into their chapter folders.")


if __name__ == "__main__":
    main()
