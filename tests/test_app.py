from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from modules.styles import BUILTIN_STYLES


class AppTests(unittest.TestCase):
    def app_path(self):
        return str(Path(__file__).resolve().parents[1] / "app.py")

    def test_custom_style_survives_new_session(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"MINI1_STYLE_DIR": folder}):
            app = AppTest.from_file(self.app_path()).run()
            app.text_input(key="new_style_name").set_value("나의 미니어처")
            for field in ("form", "palette", "costume", "environment", "mood"):
                app.text_area(key=f"new_style_{field}").set_value(f"내 설정 {field}")
            next(b for b in app.button if b.label == "내 스타일 저장").click().run()
            self.assertFalse(app.exception)
            restored = AppTest.from_file(self.app_path()).run()
            self.assertIn("나의 미니어처", restored.selectbox(key="primary_choice").options)
            self.assertTrue(any(b.label == "선택한 스타일 삭제" for b in restored.button))

    def test_styles_cast_and_reset(self):
        app = AppTest.from_file(self.app_path()).run()
        next(b for b in app.button if b.label == "프리셋 적용").click().run()
        app.selectbox(key="primary_choice").select(BUILTIN_STYLES[3].key).run()
        app.selectbox(key="secondary_choice").select(BUILTIN_STYLES[2].key).run()
        app.selectbox(key="blend_mode").select("fusion").run()
        app.number_input(key="character_count").set_value(2).run()
        app.text_input(key="char_0_identity").set_value("마리오").run()
        app.text_input(key="char_1_identity").set_value("아이언맨").run()
        next(b for b in app.button if b.label == "프롬프트 생성").click().run()
        self.assertFalse(app.exception)
        self.assertIn("Exactly 2 featured", app.code[0].value)
        self.assertIn("슈퍼 마리오", app.code[0].value)
        app.selectbox(key="primary_choice").select(BUILTIN_STYLES[2].key).run()
        self.assertEqual(app.selectbox(key="secondary_choice").value, "none")
        next(b for b in app.button if b.label == "새 작업").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.number_input(key="character_count").value, 0)
        self.assertEqual(app.selectbox(key="primary_choice").value, "none")

    def test_generate_change_video_and_disable_default_avoid(self):
        app = AppTest.from_file(self.app_path()).run()
        self.assertFalse(app.exception)
        next(b for b in app.button if b.label == "프롬프트 생성").click().run()
        self.assertEqual(len(app.error), 1)
        next(b for b in app.button if b.label == "프리셋 적용").click().run()
        app.checkbox(key="use_default_negative").uncheck().run()
        next(b for b in app.button if b.label == "프롬프트 생성").click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("watermark", app.code[0].value)
        self.assertEqual(app.code[2].value, "(제외 조건 없음)")
        app.selectbox(key="medium").select("video").run()
        self.assertEqual(len(app.warning), 1)
        app.slider(key="duration").set_value(10).run()
        next(b for b in app.button if b.label == "프롬프트 생성").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.warning), 0)
        self.assertIn("Duration: 10 seconds", app.code[0].value)
        self.assertFalse(any("platform" in s.label.lower() for s in app.selectbox))


if __name__ == "__main__":
    unittest.main()
