from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


Number = int | float


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Size:
    width: float
    height: float


@dataclass(frozen=True)
class Circle:
    center: Point
    radius: float


@dataclass(frozen=True)
class Camera2D:
    """World-to-screen transform for deterministic 2D shot composition.

    `origin` is the world-space point that maps to screen (0, 0). `scale`
    applies uniformly so physical relationships stay aligned after crops/zooms.
    """

    origin: Point = Point(0.0, 0.0)
    scale: float = 1.0

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError("camera scale must be positive")

    def point_to_screen(self, point: Point) -> Point:
        return Point(
            (point.x - self.origin.x) * self.scale,
            (point.y - self.origin.y) * self.scale,
        )

    def distance_to_screen(self, distance: Number) -> float:
        return float(distance) * self.scale


@dataclass(frozen=True)
class PortalGeometry:
    center: Point
    outer_radius: float
    inner_radius: float
    orientation_degrees: float = 0.0

    def __post_init__(self) -> None:
        if self.outer_radius <= 0:
            raise ValueError("portal outer_radius must be positive")
        if self.inner_radius <= 0:
            raise ValueError("portal inner_radius must be positive")
        if self.inner_radius >= self.outer_radius:
            raise ValueError("portal inner_radius must be smaller than outer_radius")

    def inner_circle(self, camera: Camera2D) -> Circle:
        return Circle(
            center=camera.point_to_screen(self.center),
            radius=camera.distance_to_screen(self.inner_radius),
        )

    def outer_circle(self, camera: Camera2D) -> Circle:
        return Circle(
            center=camera.point_to_screen(self.center),
            radius=camera.distance_to_screen(self.outer_radius),
        )


@dataclass(frozen=True)
class FloorAnchor:
    x: float
    floor_y: float

    @property
    def point(self) -> Point:
        return Point(self.x, self.floor_y)


@dataclass(frozen=True)
class SetGeometry:
    name: str
    floor_y: float
    anchors: Mapping[str, FloorAnchor]
    portal: PortalGeometry | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SetGeometry":
        floor = data.get("floor_y")
        if not isinstance(floor, (int, float)):
            raise ValueError("floor_y missing/non-numeric")

        anchors: dict[str, FloorAnchor] = {}
        raw_anchors = data.get("anchors", {})
        if not isinstance(raw_anchors, Mapping):
            raise ValueError("anchors must be an object")

        for name, raw in raw_anchors.items():
            if not isinstance(raw, Mapping):
                raise ValueError(f"anchor {name} must be an object")
            x = raw.get("x")
            anchor_floor = raw.get("floor_y", floor)
            if not isinstance(x, (int, float)):
                raise ValueError(f"anchor {name}.x missing/non-numeric")
            if not isinstance(anchor_floor, (int, float)):
                raise ValueError(f"anchor {name}.floor_y missing/non-numeric")
            if float(anchor_floor) != float(floor):
                raise ValueError(f"anchor {name} floor_y drifts from set floor_y")
            anchors[str(name)] = FloorAnchor(float(x), float(anchor_floor))

        portal = None
        raw_portal = data.get("portal")
        if raw_portal is not None:
            if not isinstance(raw_portal, Mapping):
                raise ValueError("portal must be an object")
            center = raw_portal.get("center")
            if not (
                isinstance(center, list)
                and len(center) == 2
                and all(isinstance(value, (int, float)) for value in center)
            ):
                raise ValueError("portal.center must be [x,y]")
            portal = PortalGeometry(
                center=Point(float(center[0]), float(center[1])),
                outer_radius=float(raw_portal.get("outer_radius", 0)),
                inner_radius=float(raw_portal.get("inner_radius", 0)),
                orientation_degrees=float(raw_portal.get("orientation_degrees", 0)),
            )

        return cls(
            name=str(data.get("set", "unnamed-set")),
            floor_y=float(floor),
            anchors=anchors,
            portal=portal,
        )

    def anchor(self, name: str) -> FloorAnchor:
        try:
            return self.anchors[name]
        except KeyError as exc:
            raise KeyError(f"unknown set anchor: {name}") from exc


@dataclass(frozen=True)
class SpritePlacement:
    """Screen-space top-left placement for a sprite anchored by a local point."""

    top_left: Point
    scale: float
    anchor_screen: Point


def place_sprite_by_local_anchor(
    *,
    world_anchor: Point,
    local_anchor_px: Point,
    camera: Camera2D,
    sprite_scale: float = 1.0,
) -> SpritePlacement:
    """Place a sprite so its local anchor lands exactly on a world-space anchor.

    A character rig should normally pass the pixel coordinate of its foot/contact
    anchor. This removes guessed bounding-box placement from scene composition.
    """

    if sprite_scale <= 0:
        raise ValueError("sprite_scale must be positive")
    anchor_screen = camera.point_to_screen(world_anchor)
    combined_scale = camera.scale * sprite_scale
    top_left = Point(
        anchor_screen.x - local_anchor_px.x * combined_scale,
        anchor_screen.y - local_anchor_px.y * combined_scale,
    )
    return SpritePlacement(
        top_left=top_left,
        scale=combined_scale,
        anchor_screen=anchor_screen,
    )
