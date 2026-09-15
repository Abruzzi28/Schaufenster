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
ABFOLGE_JS_PATH = ROOT / "abfolge.js"
INDEX_PATH = ROOT / "index.html"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SKIP_DIRS = {".git", ".github", ".cursor", "node_modules"}
PREFERRED_KEYWORDS = ["Karneval", "Teamfotos", "Martinimarkt"]
MARKER_START = "/* SLIDESHOW_ABFOLGE_BEGIN */"
MARKER_END = "/* SLIDESHOW_ABFOLGE_END */"


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
    ordered = []
    for keyword in PREFERRED_KEYWORDS:
        for name in found:
            if keyword.casefold() in name.casefold() and name not in ordered:
                ordered.append(name)
    for name in load_abfolge() + list(found):
        if name in found and name not in ordered:
            ordered.append(name)

    bilder = {}
    for name in ordered:
        images = folder_images(found[name])
        bilder[name] = images
        (found[name] / "bilder.json").write_text(
            json.dumps(images, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{name}: {len(images)} Bilder")

    payload = {"ordner": ordered, "bilder": bilder}
    payload_js = "window.SLIDESHOW_ABFOLGE = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    ABFOLGE_PATH.write_text(
        json.dumps({"ordner": ordered}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ABFOLGE_JS_PATH.write_text(payload_js, encoding="utf-8")

    html = INDEX_PATH.read_text(encoding="utf-8")
    start = html.find(MARKER_START)
    end = html.find(MARKER_END)
    if start != -1 and end != -1 and end > start:
        injected = (
            MARKER_START
            + "\n        "
            + payload_js.strip()
            + "\n        "
            + MARKER_END
        )
        html = html[:start] + injected + html[end + len(MARKER_END):]
        INDEX_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
