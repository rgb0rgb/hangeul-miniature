from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest

from modules.compiler import build_prompt
from modules.styles import (
    BUILTIN_STYLES,
    StyleSpec,
    delete_style,
    read_styles,
    replace_style,
    save_style,
)
from modules.templates import CharacterSpec, PRESETS, dump_project, load_project


class StyleTests(unittest.TestCase):
    def setUp(self):
        self.base = PRESETS["철도 디오라마"]
        self.primary = BUILTIN_STYLES[3]
        self.secondary = BUILTIN_STYLES[2]

    def test_every_ordered_pair_and_blend_compiles(self):
        for a in BUILTIN_STYLES:
            for b in BUILTIN_STYLES:
                if a == b:
                    continue
                for mode in ("accent", "split", "fusion"):
                    with self.subTest(a=a.name, b=b.name, mode=mode):
                        params = replace(
                            self.base,
                            primary_style=a,
                            secondary_style=b,
                            blend_mode=mode,
                        )
                        result = build_prompt(params)
                        self.assertIn(a.name, result.positive)
                        self.assertIn(b.name, result.positive)
                        self.assertIn(
                            "Preserve the explicit scene, subject and character identity first",
                            result.positive,
                        )
                        self.assertEqual(params, load_project(dump_project(params)))

    def test_accent_does_not_import_secondary_anatomy_or_world(self):
        result = build_prompt(
            replace(
                self.base,
                primary_style=self.primary,
                secondary_style=self.secondary,
            )
        )
        self.assertIn(self.primary.form, result.positive)
        self.assertIn(self.secondary.palette, result.positive)
        self.assertNotIn(self.secondary.form, result.positive)
        self.assertNotIn(self.secondary.environment, result.positive)

    def test_split_assigns_secondary_only_to_environment(self):
        result = build_prompt(
            replace(
                self.base,
                primary_style=self.primary,
                secondary_style=self.secondary,
                blend_mode="split",
            )
        )
        self.assertIn(self.secondary.environment, result.positive)
        self.assertNotIn(self.secondary.form, result.positive)
        self.assertNotIn(self.secondary.costume, result.positive)
        self.assertNotIn("30%", result.positive)

    def test_fusion_weight_and_primary_conflict_resolution(self):
        result = build_prompt(
            replace(
                self.base,
                primary_style=self.primary,
                secondary_style=self.secondary,
                blend_mode="fusion",
                secondary_weight=40,
            )
        )
        self.assertIn("60% primary and 40% secondary", result.positive)
        self.assertIn(
            "If anatomy or shapes conflict, retain the primary design",
            result.positive,
        )

    def test_character_identity_and_video_continuity(self):
        cast = (
            CharacterSpec("마리오", "빨간 모자", "웃음", "손 흔들기", "작은 꽃", "왼쪽"),
            CharacterSpec(
                "아이언맨", "붉은 갑옷", "친근한 눈빛", "서 있기", "작은 공구", "오른쪽"
            ),
        )
        params = replace(self.base, characters=cast, medium="video")
        result = build_prompt(params)
        for character in cast:
            for value in asdict(character).values():
                self.assertIn(value, result.positive)
        self.assertIn("Exactly 2 featured", result.positive)
        self.assertIn("Across frames, lock", result.positive)
        self.assertIn("shared readable focus region", result.positive)
        self.assertEqual(params, load_project(dump_project(params)))

    def test_legacy_v2_migration(self):
        data = asdict(self.base)
        for key in (
            "primary_style",
            "secondary_style",
            "blend_mode",
            "secondary_weight",
            "characters",
            "action_source",
            "action_context",
            "use_default_negative",
        ):
            data.pop(key)
        self.assertEqual(
            load_project(json.dumps({"version": 2, "params": data})),
            self.base,
        )

    def test_custom_style_is_portable_and_persistent(self):
        style = StyleSpec("내 스타일", "각진 형태", "청록색", "외투", "작은 항구", "차분함")
        with tempfile.TemporaryDirectory() as folder:
            save_style(folder, style)
            save_style(folder, style)
            styles, errors = read_styles(folder)
            self.assertEqual(styles, [style])
            self.assertFalse(errors)
        params = replace(self.base, primary_style=style)
        restored = load_project(dump_project(params))
        self.assertIn("각진 형태", build_prompt(restored).positive)

    def test_custom_style_can_be_replaced_and_deleted(self):
        old = StyleSpec("오래된 이름", "형태", "색감", "의상", "배경", "분위기")
        new = StyleSpec("수정된 이름", "새 형태", "새 색감", "새 의상", "새 배경", "새 분위기")
        with tempfile.TemporaryDirectory() as folder:
            save_style(folder, old)
            replace_style(folder, old, new)
            styles, errors = read_styles(folder)
            self.assertFalse(errors)
            self.assertEqual(styles, [new])
            self.assertFalse((Path(folder) / f"{old.key}.json").exists())
            delete_style(folder, new)
            self.assertEqual(read_styles(folder), ([], []))

    def test_invalid_nested_data_rejected(self):
        changes_list = (
            {"characters": (CharacterSpec(""),)},
            {"characters": ({"identity": "x"},)},
            {"characters": (CharacterSpec("x"),) * 7},
            {"secondary_style": self.secondary},
            {"primary_style": self.primary, "secondary_style": self.primary},
            {"secondary_weight": True},
        )
        for changes in changes_list:
            with self.subTest(changes=str(changes)):
                with self.assertRaises(ValueError):
                    build_prompt(replace(self.base, **changes))
        data = json.loads(dump_project(self.base))
        data["params"]["characters"] = [{"identity": "x"}]
        with self.assertRaises(ValueError):
            load_project(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
