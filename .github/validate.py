"""Fails the build on broken JSON or references to custom models/textures that don't exist.

Usage: python .github/validate.py <pack_dir>  (run on the merged base + addon pack)
Only references into subfolders (e.g. block/key_blocks/info) are checked, top-level
ones (block/stone) may point at vanilla assets, which aren't in this repo.
"""
import json
import pathlib
import sys

pack = pathlib.Path(sys.argv[1])
assets = pack / "assets/minecraft"
errors = []


def is_custom(ref):
    return ref.removeprefix("minecraft:").count("/") > 1


def check(ref, kind, ext, src):
    path = assets / kind / (ref.removeprefix("minecraft:") + ext)
    if is_custom(ref) and not path.is_file():
        errors.append(f"{src}: missing {kind[:-1]} '{ref}'")


def walk(node, src):
    # model refs live under "model"/"parent" keys anywhere in blockstates, items and models
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("model", "parent") and isinstance(value, str):
                check(value, "models", ".json", src)
            elif key == "textures" and isinstance(value, dict):
                for tex in value.values():
                    if not tex.startswith("#"):
                        check(tex, "textures", ".png", src)
            else:
                walk(value, src)
    elif isinstance(node, list):
        for item in node:
            walk(item, src)


for f in sorted([*pack.rglob("*.json"), *pack.rglob("*.mcmeta")]):
    src = f.relative_to(pack).as_posix()
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        errors.append(f"{src}: invalid JSON ({e})")
        continue
    walk(data, src)

print("\n".join(errors) or f"{pack}: OK")
sys.exit(1 if errors else 0)
