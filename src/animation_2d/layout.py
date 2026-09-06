from __future__ import annotations

from dataclasses import dataclass

from src.core.geometry import (
    Camera2D,
    Circle,
    Point,
    SetGeometry,
    SpritePlacement,
    place_sprite_by_local_anchor,
)


@dataclass(frozen=True)
class CharacterRigLayout:
    """Minimal spatial metadata required to ground a 2D character rig."""

    foot_anchor_px: Point


@dataclass(frozen=True)
class CharacterScenePlacement:
    character: str
    set_anchor: str
    placement: SpritePlacement


@dataclass(frozen=True)
class PortalScenePlacement:
    """Physical portal frame and energy effect derived from one geometry source."""

    frame_outer: Circle
    frame_inner: Circle
    energy: Circle
    orientation_degrees: float


def place_character(
    *,
    character: str,
    set_geometry: SetGeometry,
    set_anchor: str,
    rig: CharacterRigLayout,
    camera: Camera2D,
    sprite_scale: float = 1.0,
) -> CharacterScenePlacement:
    anchor = set_geometry.anchor(set_anchor)
    placement = place_sprite_by_local_anchor(
        world_anchor=anchor.point,
        local_anchor_px=rig.foot_anchor_px,
        camera=camera,
        sprite_scale=sprite_scale,
    )
    return CharacterScenePlacement(
        character=character,
        set_anchor=set_anchor,
        placement=placement,
    )


def place_portal(*, set_geometry: SetGeometry, camera: Camera2D) -> PortalScenePlacement:
    portal = set_geometry.portal
    if portal is None:
        raise ValueError("set has no portal geometry")

    outer = portal.outer_circle(camera)
    inner = portal.inner_circle(camera)

    # Energy does not get its own guessed center/radius. It inherits the physical
    # portal opening exactly, which is the visual defect this architecture exists
    # to prevent.
    energy = Circle(center=inner.center, radius=inner.radius)

    return PortalScenePlacement(
        frame_outer=outer,
        frame_inner=inner,
        energy=energy,
        orientation_degrees=portal.orientation_degrees,
    )
