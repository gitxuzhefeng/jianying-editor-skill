#!/usr/bin/env python3
"""星空粒子片头：Web 录屏 → 剪映草稿导入"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SCRIPTS_PATH = os.path.join(REPO_ROOT, "scripts")

if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)

if sys.platform == "darwin":
    homebrew_bin = "/opt/homebrew/bin"
    if homebrew_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = homebrew_bin + ":" + os.environ.get("PATH", "")

from jy_wrapper import JyProject

HTML_PATH = os.path.join(CURRENT_DIR, "starfield_intro.html")
PROJECT_NAME = "星空粒子片头"


def main() -> None:
    if not os.path.exists(HTML_PATH):
        raise FileNotFoundError(f"HTML not found: {HTML_PATH}")

    project = JyProject(project_name=PROJECT_NAME, overwrite=True)

    print("正在录制 5 秒星空粒子片头并导入剪映时间轴...")
    seg = project.add_web_asset_safe(
        html_path=HTML_PATH,
        start_time="0s",
        duration="5s",
        track_name="VideoTrack",
        width=1920,
        height=1080,
    )
    if seg is None:
        raise RuntimeError("Web-to-Video 录制失败，请确认已安装 playwright: pip install playwright && playwright install chromium")

    result = project.save()
    draft_path = result.get("draft_path", "")
    print(f"\n完成！剪映草稿已生成：{draft_path}")
    print(f"请在剪映中打开草稿「{PROJECT_NAME}」")
    print("提示：若列表未刷新，请重启剪映或随便打开一个旧草稿再返回。")


if __name__ == "__main__":
    main()
