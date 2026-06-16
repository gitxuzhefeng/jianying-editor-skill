"""TTS 配音 + 智能字幕对齐演示（本地素材版）。"""

import os

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


def main() -> None:
    project_name = "TTS_Narrated_Subtitles_Demo"
    assets_dir = os.path.join(SKILL_ROOT, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    bgm_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path):
        print(f"Demo video not found: {video_path}")
        return

    print(f"Creating project: {project_name}")
    project = JyProject(project_name=project_name, overwrite=True)

    narration = (
        "欢迎来到剪映自动化试剪。"
        "今天我们演示智能配音与字幕对齐。"
        "每一句旁白都会自动生成语音，并精准落在字幕轨道上。"
    )

    print("Adding background video...")
    project.add_media_safe(video_path, start_time="0s", track_name="VideoTrack")

    print("Generating TTS + aligned subtitles...")
    end_cursor = project.add_narrated_subtitles(
        text=narration,
        speaker="zh_female_xiaopengyou",
        start_time="0.5s",
        track_name="Subtitles",
    )

    if os.path.exists(bgm_path):
        print("Adding background music (ducked to 60%)...")
        bgm_duration_s = max(5.0, (end_cursor / 1_000_000) + 0.5)
        bgm_seg = project.add_media_safe(
            bgm_path,
            start_time="0s",
            duration=f"{bgm_duration_s:.1f}s",
            track_name="BGM",
        )
        if bgm_seg is not None:
            bgm_seg.volume = 0.6

    print("Adding title...")
    project.add_text_simple(
        "TTS + 智能字幕 Demo",
        start_time="0.1s",
        duration="2.5s",
        track_name="TitleTrack",
        anim_in="复古打字机",
    )

    print("Saving project...")
    result = project.save()
    draft_path = result.get("draft_path", "")
    print(f"Done. Open JianYing and find draft: {project_name}")
    if draft_path:
        print(f"Draft path: {draft_path}")


if __name__ == "__main__":
    main()
