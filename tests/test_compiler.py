from dataclasses import replace
import json
import unittest
from modules.compiler import build_prompt
from modules.templates import OPTIONS, PRESETS, dump_project, load_project


class CompilerTests(unittest.TestCase):
    def setUp(self):
        self.params = PRESETS["철도 디오라마"]

    def test_all_choices_compile_and_round_trip(self):
        for name, choices in OPTIONS.items():
            for value in choices:
                with self.subTest(name=name, value=value):
                    params = replace(self.params, **{name: value})
                    self.assertEqual(load_project(dump_project(params)), params)
                    self.assertIn(params.scene, build_prompt(params).positive)

    def test_image_omits_motion(self):
        result = build_prompt(replace(self.params, action="UNIQUE_ACTION", movement="orbit"))
        self.assertNotIn("UNIQUE_ACTION", result.combined)
        self.assertNotIn("Duration", result.combined)
        self.assertNotIn("MOTION", result.combined)

    def test_video_includes_temporal_direction(self):
        result = build_prompt(replace(self.params, medium="video", duration=12))
        self.assertIn("Duration: 12 seconds", result.positive)
        self.assertIn("Follow the events described in SCENE", result.positive)
        self.assertNotIn("The model remains still", result.positive)
        self.assertIn("temporal flicker", result.negative)

    def test_default_avoid_can_be_disabled(self):
        result = build_prompt(replace(self.params, negative="내가 지정한 제외"), include_default_negative=False)
        self.assertEqual(result.negative, "내가 지정한 제외")
        self.assertNotIn("watermark", result.combined)
        self.assertIn("기본 제외 조건을 사용하지 않았습니다", result.notes[1])
        empty = build_prompt(self.params, include_default_negative=False)
        self.assertEqual(empty.negative, "")
        self.assertNotIn("AVOID\n", empty.combined)

    def test_clean_and_deep_are_consistent(self):
        result = build_prompt(replace(self.params, wear="pristine", detail="intricate", focus="deep"))
        self.assertIn("no dirt, scratches", result.positive)
        self.assertNotIn("Selective depth of field:", result.positive)
        self.assertIn("shallow depth of field", result.negative)

    def test_literal_input_is_preserved(self):
        literal = '${alert(1)} ` & <script> 테스트'
        self.assertIn(literal, build_prompt(replace(self.params, scene=literal)).positive)

    def test_invalid_inputs(self):
        for change in [{"scene": " "}, {"subject": ""}, {"duration": True}, {"duration": 31}, {"scale": "bad"}, {"cue": []}, {"scene": "x" * 6001}]:
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError):
                    build_prompt(replace(self.params, **change))
        with self.assertRaises(ValueError):
            build_prompt(self.params, include_default_negative="no")

    def test_invalid_projects(self):
        for data in [b"\xff", "{", "[]", '{"version":true}', '{"version":2,"params":{}}', " " * 500001]:
            with self.assertRaises(ValueError):
                load_project(data)
        data = json.loads(dump_project(self.params))
        data["params"]["unexpected"] = 1
        with self.assertRaises(ValueError):
            load_project(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
