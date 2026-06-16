"""桌面工作区路径：草稿、导出、生成素材与业务脚本。"""

import os
import shutil
import sys
import time
from typing import Optional

WORKSPACE_DIRNAME = "JianYing-Workspace"
SUBDIRS = ("drafts", "exports", "media", "scripts")


def get_workspace_root(explicit: Optional[str] = None) -> str:
    root = (explicit or os.getenv("JY_WORKSPACE_ROOT", "")).strip()
    if not root:
        root = os.path.join(os.path.expanduser("~"), "Desktop", WORKSPACE_DIRNAME)
    return os.path.abspath(root)


def get_drafts_dir(workspace_root: Optional[str] = None) -> str:
    override = os.getenv("JY_PROJECTS_ROOT", "").strip()
    if override:
        return os.path.abspath(override)
    # macOS 剪映无法稳定打开桌面目录下的草稿或符号链接，草稿必须落在原生目录。
    if os.name == "posix" and sys.platform == "darwin":
        from utils.formatters import _detect_native_jianying_drafts_root

        return _detect_native_jianying_drafts_root()
    return os.path.join(get_workspace_root(workspace_root), "drafts")


def get_exports_dir(workspace_root: Optional[str] = None) -> str:
    override = os.getenv("JY_EXPORT_DIR", "").strip()
    if override:
        return os.path.abspath(override)
    return os.path.join(get_workspace_root(workspace_root), "exports")


def get_media_dir(workspace_root: Optional[str] = None) -> str:
    override = os.getenv("JY_MEDIA_DIR", "").strip()
    if override:
        return os.path.abspath(override)
    return os.path.join(get_workspace_root(workspace_root), "media")


def get_user_scripts_dir(workspace_root: Optional[str] = None) -> str:
    return os.path.join(get_workspace_root(workspace_root), "scripts")


def ensure_workspace_layout(workspace_root: Optional[str] = None) -> str:
    root = get_workspace_root(workspace_root)
    for name in SUBDIRS:
        os.makedirs(os.path.join(root, name), exist_ok=True)
    return root


def apply_workspace_env(workspace_root: Optional[str] = None) -> str:
    """在未显式设置时，将草稿/导出/素材默认指向桌面工作区。"""
    root = ensure_workspace_layout(workspace_root)
    os.environ.setdefault("JY_WORKSPACE_ROOT", root)
    os.environ.setdefault("JY_PROJECTS_ROOT", get_drafts_dir(root))
    os.environ.setdefault("JY_EXPORT_DIR", get_exports_dir(root))
    os.environ.setdefault("JY_MEDIA_DIR", get_media_dir(root))
    return root


def should_replace_native_draft_conflict() -> bool:
    return os.getenv("JY_WORKSPACE_REPLACE_CONFLICT", "1") == "1"


def backup_native_draft_conflict(draft_name: str, native_draft_path: str) -> str:
    backup_root = os.path.join(get_exports_dir(), ".draft-conflicts")
    os.makedirs(backup_root, exist_ok=True)
    backup_path = os.path.join(backup_root, f"{draft_name}-{int(time.time())}")
    shutil.move(native_draft_path, backup_path)
    return backup_path


def default_export_path(draft_name: str, ext: str = "mp4") -> str:
    safe_name = draft_name.replace(os.sep, "_").strip() or "output"
    return os.path.join(get_exports_dir(), f"{safe_name}.{ext}")


def get_workspace_drafts_mirror(workspace_root: Optional[str] = None) -> str:
    """桌面工作区中的草稿镜像目录（仅供备份/查看，剪映不直接读取）。"""
    return os.path.join(get_workspace_root(workspace_root), "drafts")


def mirror_draft_to_workspace(draft_path: str, draft_name: str) -> Optional[str]:
    """将已保存草稿复制到桌面工作区 drafts/ 镜像目录。"""
    if not os.path.isdir(draft_path):
        return None
    mirror_root = get_workspace_drafts_mirror()
    os.makedirs(mirror_root, exist_ok=True)
    mirror_path = os.path.join(mirror_root, draft_name)
    if os.path.islink(mirror_path):
        os.unlink(mirror_path)
    shutil.copytree(draft_path, mirror_path, dirs_exist_ok=True)
    return mirror_path
