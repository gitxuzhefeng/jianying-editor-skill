import os
import json
import uuid
import shutil
import pyJianYingDraft as draft

class MockVideoMaterial(draft.VideoMaterial):
    def __init__(self, material_id, duration, name, path):
        self.material_id = material_id
        self.duration = duration
        self.material_name = name
        self.path = path
    def serialize(self):
        return {
            "id": self.material_id, "type": "video", "name": self.material_name, "path": self.path,
            "duration": self.duration, "material_id": self.material_id
        }

class MockAudioMaterial(draft.AudioMaterial):
    def __init__(self, material_id, duration, name, path):
        self.material_id = material_id
        self.duration = duration
        self.material_name = name
        self.path = path
    def serialize(self):
        return {
            "id": self.material_id, "type": "audio", "name": self.material_name, "path": self.path,
            "duration": self.duration, "material_id": self.material_id
        }

class CompoundSegment:
    def __init__(self, material_id, target_timerange):
        self.material_id = material_id
        self.target_timerange = target_timerange
    def serialize(self):
        return {
             "id": str(uuid.uuid4()).upper(), "material_id": self.material_id,
             "target_timerange": self.target_timerange.serialize(),
             "render_index": 0, "type": "video"
        }

class MockingOpsMixin:
    """
    JyProject 的协议补丁与伪物料 Mixin。
    """
    def _force_activate_adjustments(self):
        content_path = os.path.join(self.root, self.name, "draft_info.json")
        if not os.path.exists(content_path):
            content_path = os.path.join(self.root, self.name, "draft_content.json")
        if not os.path.exists(content_path): return

        try:
            with open(content_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            has_modified = False
            materials = data.setdefault("materials", {})
            all_effects = materials.setdefault("effects", [])

            PROP_MAP = {"KFTypeBrightness": "brightness", "KFTypeContrast": "contrast", "KFTypeSaturation": "saturation"}
            jy_res_path = "C:/Program Files/JianyingPro/5.9.0.11632/Resources/DefaultAdjustBundle/combine_adjust"

            for track in data.get("tracks", []):
                for seg in track.get("segments", []):
                    kfs = seg.get("common_keyframes", [])
                    active_props = [kf.get("property_type") for kf in kfs if kf.get("property_type") in PROP_MAP]

                    if active_props:
                        seg["enable_adjust"] = True
                        seg["enable_color_correct_adjust"] = True
                        refs = seg.setdefault("extra_material_refs", [])

                        for prop in active_props:
                            mat_type = PROP_MAP[prop]
                            if not any(m.get("type") == mat_type and m["id"] in refs for m in all_effects):
                                new_id = str(uuid.uuid4()).upper()
                                shadow_mat = {
                                    "type": mat_type, "value": 0.0, "path": jy_res_path, "id": new_id,
                                    "apply_target_type": 0, "platform": "all", "source_platform": 0, "version": "v2"
                                }
                                all_effects.append(shadow_mat)
                                refs.append(new_id)
                                has_modified = True

            if has_modified:
                with open(content_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Force activation failed: {e}")

    def _patch_cloud_material_ids(self):
        if not self._cloud_audio_patches and not self._cloud_text_patches: return
        content_path = os.path.join(self.root, self.name, "draft_info.json")
        if not os.path.exists(content_path):
            content_path = os.path.join(self.root, self.name, "draft_content.json")
        if not os.path.exists(content_path): return

        try:
            with open(content_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            has_modified = False
            materials = data.get("materials", {})
            audios = materials.get("audios", [])
            for mat in audios:
                path = mat.get("path", "")
                for dummy_path, patch_info in self._cloud_audio_patches.items():
                    if dummy_path in path:
                        if patch_info["type"] == "music":
                            mat["music_id"] = patch_info["id"]
                            mat["type"] = "music"
                            has_modified = True
            
            if has_modified:
                with open(content_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def _patch_flower_text_styles(self):
        if not self._cloud_text_patches:
            return

        draft_path = os.path.join(self.root, self.name)
        content_path = os.path.join(draft_path, "draft_info.json")
        if not os.path.exists(content_path):
            content_path = os.path.join(draft_path, "draft_content.json")
        if not os.path.exists(content_path):
            return

        try:
            from utils.skill_path import resolve_skill_root

            skill_root, _ = resolve_skill_root(os.path.join(os.path.dirname(__file__), ".."))
            if not skill_root:
                env_root = os.getenv("JY_SKILL_ROOT", "").strip()
                skill_root = env_root if env_root else None
            if not skill_root:
                return

            with open(content_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            texts = data.get("materials", {}).get("texts", [])
            has_modified = False
            for mat in texts:
                mid = mat.get("id")
                style_id = self._cloud_text_patches.get(mid)
                if not style_id:
                    continue

                src_style_dir = os.path.join(skill_root, "assets", "artistEffect", style_id)
                if not os.path.isdir(src_style_dir):
                    continue

                dest_style_dir = os.path.join(draft_path, "materials", "artistEffect", style_id)
                shutil.copytree(src_style_dir, dest_style_dir, dirs_exist_ok=True)

                effect_subdir = None
                for name in os.listdir(dest_style_dir):
                    candidate = os.path.join(dest_style_dir, name)
                    if os.path.isdir(candidate):
                        effect_subdir = candidate
                        break
                if not effect_subdir:
                    effect_subdir = dest_style_dir

                raw = mat.get("content", "")
                if not raw:
                    continue
                content = json.loads(raw)
                styles = content.get("styles", [])
                if not styles:
                    continue
                styles[0]["effectStyle"] = {"id": style_id, "path": effect_subdir}
                mat["content"] = json.dumps(content, ensure_ascii=False)
                has_modified = True

            if has_modified:
                with open(content_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[warn] flower text patch failed: {e}")
