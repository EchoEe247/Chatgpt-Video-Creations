import copy
import json
import pathlib
import unittest

from src.core.scene_plan import validate_scene_plan

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/new-episode/scene-plan.json").read_text())


class ScenePlanTests(unittest.TestCase):
    def test_template_is_valid(self):
        self.assertEqual(validate_scene_plan(TEMPLATE), [])

    def test_overlap_is_rejected(self):
        data = copy.deepcopy(TEMPLATE)
        second = copy.deepcopy(data["scenes"][0])
        second["id"] = "scene-002"
        second["start"] = 7.0
        data["scenes"].append(second)
        self.assertTrue(any("overlaps" in error for error in validate_scene_plan(data)))

    def test_review_point_must_be_inside_scene(self):
        data = copy.deepcopy(TEMPLATE)
        data["scenes"][0]["review_points"][0]["at_seconds"] = 9.0
        self.assertTrue(any("outside scene duration" in error for error in validate_scene_plan(data)))


if __name__ == "__main__":
    unittest.main()
