"""保存前将草稿内引用的外部素材复制进草稿目录，避免剪映找不到文件。"""

import json
import os
import shutil
from typing import Iterable, Tuple


def _content_json_paths(draft_path: str) -> Iterable[str]:
    for name in ("draft_info.json", "draft_content.json"):
        path = os.path.join(draft_path, name)
        if os.path.exists(path):
            yield path


def relocate_external_materials(draft_path: str) -> int:
    """复制草稿目录外的素材到 draft_path/materials/ 并改写 JSON 路径。"""
    draft_path = os.path.abspath(draft_path)
    materials_dir = os.path.join(draft_path, "materials")
    os.makedirs(materials_dir, exist_ok=True)
    relocated = 0

    for content_path in _content_json_paths(draft_path):
        with open(content_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        for kind in ("videos", "audios", "images"):
            for mat in data.get("materials", {}).get(kind, []):
                src = mat.get("path", "")
                if not src or not os.path.isfile(src):
                    continue
                try:
                    if os.path.commonpath([draft_path, os.path.abspath(src)]) == draft_path:
                        continue
                except ValueError:
                    pass

                base = os.path.basename(src)
                stem, ext = os.path.splitext(base)
                dest = os.path.join(materials_dir, base)
                counter = 1
                while os.path.exists(dest) and os.path.abspath(dest) != os.path.abspath(src):
                    dest = os.path.join(materials_dir, f"{stem}_{counter}{ext}")
                    counter += 1

                if not os.path.exists(dest):
                    shutil.copy2(src, dest)
                mat["path"] = dest
                changed = True
                relocated += 1

        if changed:
            with open(content_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    return relocated
