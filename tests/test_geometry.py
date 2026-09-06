import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.animation_2d.layout import CharacterRigLayout, place_character, place_portal
from src.core.geometry import Camera2D, Point, SetGeometry


SAMPLE = {
    "schema_version": 1,
    "set": "example-lab",
    "floor_y": 438,
    "anchors": {
        "vex_start": {"x": 230, "floor_y": 438},
        "milo_start": {"x": 550, "floor_y": 438},
    },
    "portal": {
        "center": [702, 220],
        "outer_radius": 120,
        "inner_radius": 94,
        "orientation_degrees": 0,
    },
}


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.set_geometry = SetGeometry.from_mapping(SAMPLE)

    def test_character_foot_anchor_lands_on_floor(self):
        camera = Camera2D()
        rig = CharacterRigLayout(foot_anchor_px=Point(50, 100))
        result = place_character(
            character="Vex",
            set_geometry=self.set_geometry,
            set_anchor="vex_start",
            rig=rig,
            camera=camera,
        )
        self.assertEqual(result.placement.anchor_screen, Point(230, 438))
        self.assertEqual(result.placement.top_left, Point(180, 338))

    def test_camera_crop_moves_character_anchor_and_floor_together(self):
        camera = Camera2D(origin=Point(100, 50), scale=2.0)
        rig = CharacterRigLayout(foot_anchor_px=Point(50, 100))
        result = place_character(
            character="Vex",
            set_geometry=self.set_geometry,
            set_anchor="vex_start",
            rig=rig,
            camera=camera,
            sprite_scale=0.5,
        )
        self.assertEqual(result.placement.anchor_screen, Point(260, 776))
        self.assertEqual(result.placement.scale, 1.0)
        self.assertEqual(result.placement.top_left, Point(210, 676))

    def test_portal_energy_inherits_physical_opening(self):
        camera = Camera2D(origin=Point(200, 20), scale=1.5)
        result = place_portal(set_geometry=self.set_geometry, camera=camera)
        self.assertEqual(result.energy.center, result.frame_inner.center)
        self.assertEqual(result.energy.radius, result.frame_inner.radius)
        self.assertEqual(result.energy.center, Point(753, 300))
        self.assertEqual(result.energy.radius, 141)

    def test_rejects_anchor_floor_drift(self):
        broken = json.loads(json.dumps(SAMPLE))
        broken["anchors"]["vex_start"]["floor_y"] = 430
        with self.assertRaisesRegex(ValueError, "drifts from set floor_y"):
            SetGeometry.from_mapping(broken)

    def test_rejects_portal_inner_radius_larger_than_outer(self):
        broken = json.loads(json.dumps(SAMPLE))
        broken["portal"]["inner_radius"] = 130
        with self.assertRaisesRegex(ValueError, "inner_radius must be smaller"):
            SetGeometry.from_mapping(broken)


if __name__ == "__main__":
    unittest.main()
