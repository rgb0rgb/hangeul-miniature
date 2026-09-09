from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from modules.compiler import build_prompt
from modules.templates import PRESETS, action_context, dump_project, load_project


SCENE = "우주선이 산악지대에 도착 한 후 우주인들이 문을 열고 나온다. 주위에 수 십명의 사람들이 모여 있다."
SUBJECT = "우주선이 착륙하는 모습."
OLD_ACTION = "기관차가 터널을 빠져나와 천천히 앞으로 이동한다."


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.params = replace(
            PRESETS["철도 디오라마"],
            scene=SCENE,
            subject=SUBJECT,
            medium="video",
        )

    def test_reported_stale_action_is_not_emitted(self):
        result = build_prompt(replace(self.params, action=OLD_ACTION))
        self.assertIn(SCENE, result.positive)
        self.assertNotIn("기관차", result.combined)
        self.assertNotIn("터널", result.combined)
        self.assertNotIn("The model remains still", result.combined)
        self.assertIn(
            "Follow the events described in SCENE in their stated order",
            result.positive,
        )

    def test_explicit_action_is_bound_to_scene_and_subject(self):
        action = "우주선 문이 열리고 우주인들이 내려온다."
        params = replace(
            self.params,
            action=action,
            action_source="custom",
            action_context=action_context(SCENE, SUBJECT),
        )
        self.assertIn(action, build_prompt(params).positive)
        self.assertEqual(params, load_project(dump_project(params)))
        for change in ({"scene": "바다 위를 항해하는 배"}, {"subject": "작은 범선"}):
            result = build_prompt(replace(params, **change))
            self.assertNotIn(action, result.positive)
            self.assertIn("Follow the events described in SCENE", result.positive)

    def test_old_v2_and_v3_files_do_not_reactivate_stale_action(self):
        for version in (2, 3):
            values = asdict(replace(self.params, action=OLD_ACTION))
            for key in ("action_source", "action_context", "use_default_negative"):
                values.pop(key)
            if version == 2:
                for key in (
                    "primary_style",
                    "secondary_style",
                    "blend_mode",
                    "secondary_weight",
                    "characters",
                ):
                    values.pop(key)
            restored = load_project(json.dumps({"version": version, "params": values}))
            self.assertEqual(restored.action, OLD_ACTION)
            self.assertEqual(restored.action_source, "scene")
            self.assertTrue(restored.use_default_negative)
            self.assertNotIn(OLD_ACTION, build_prompt(restored).combined)

    def test_ui_scene_and_subject_edits_reset_custom_action(self):
        path = str(Path(__file__).resolve().parents[1] / "app.py")
        for field, replacement in (("scene", SCENE), ("subject", SUBJECT)):
            with self.subTest(field=field):
                app = AppTest.from_file(path).run()
                next(b for b in app.button if b.label == "프리셋 적용").click().run()
                app.selectbox(key="medium").select("video").run()
                app.selectbox(key="action_source").select("custom").run()
                app.text_area(key="action").set_value(OLD_ACTION).run()
                widget = (
                    app.text_area(key=field)
                    if field == "scene"
                    else app.text_input(key=field)
                )
                widget.set_value(replacement).run()
                self.assertEqual(app.text_area(key="action").value, "")
                self.assertEqual(app.selectbox(key="action_source").value, "scene")
                self.assertTrue(app.text_area(key="action").disabled)
                next(b for b in app.button if b.label == "프롬프트 생성").click().run()
                self.assertFalse(app.exception)
                self.assertNotIn(OLD_ACTION, app.code[0].value)

    def test_unrelated_camera_edits_preserve_explicit_action(self):
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "app.py")
        ).run()
        app.text_area(key="scene").set_value(SCENE).run()
        app.text_input(key="subject").set_value(SUBJECT).run()
        app.selectbox(key="medium").select("video").run()
        app.selectbox(key="action_source").select("custom").run()
        action = "문이 열리고 우주인 두 명이 나온다."
        app.text_area(key="action").set_value(action).run()
        app.selectbox(key="lighting").select("night").run()
        next(b for b in app.button if b.label == "프롬프트 생성").click().run()
        self.assertFalse(app.exception)
        self.assertIn(action, app.code[0].value)


if __name__ == "__main__":
    unittest.main()
