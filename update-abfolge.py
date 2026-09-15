#!/usr/bin/env python3
"""Baut die Slideshow-Listen aus den Event-Ordnern.

Jeder Unterordner mit Bildern ist ein Event. Die Reihenfolge steht in
abfolge.json (neue Ordner werden ans Ende gehängt). Innerhalb eines
Ordners zählen die Dateinamen in natürlicher Reihenfolge
(1, 2, 10 statt 1, 10, 2).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ABFOLGE_PATH = ROOT / "abfolge.json"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SKIP_DIRS = {".git", ".github", ".cursor", "node_modules"}


def natural_key(name: str):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", name)]


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and path.name.lower() != "logo.png"


def event_folders() -> list[Path]:
    folders = []
    for child in ROOT.iterdir():
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        if any(is_image(item) for item in child.iterdir()):
            folders.append(child)
    return folders


def folder_images(folder: Path) -> list[str]:
    names = [item.name for item in folder.iterdir() if is_image(item)]
    names.sort(key=natural_key)
    return names


def load_abfolge() -> list[str]:
    if not ABFOLGE_PATH.exists():
        return []
    data = json.loads(ABFOLGE_PATH.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(item) for item in data]
    return [str(item) for item in data.get("ordner", [])]


def main() -> None:
    found = {folder.name: folder for folder in event_folders()}
    ordered = [name for name in load_abfolge() if name in found]
    for name in found:
        if name not in ordered:
            ordered.append(name)

    ABFOLGE_PATH.write_text(
        json.dumps({"ordner": ordered}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for name in ordered:
        folder = found[name]
        images = folder_images(folder)
        (folder / "bilder.json").write_text(
            json.dumps(images, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{name}: {len(images)} Bilder")


if __name__ == "__main__":
    main()
