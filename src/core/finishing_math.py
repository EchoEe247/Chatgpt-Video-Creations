"""Pure NumPy math for deterministic local finishing processors."""
from __future__ import annotations

import numpy as np


def depth_atmosphere_rgb(
    rgb: np.ndarray,
    depth: np.ndarray,
    *,
    near: float = 0.0,
    density: float = 0.03,
    max_amount: float = 0.72,
    color=(0.08, 0.12, 0.18),
) -> np.ndarray:
    if rgb.ndim != 3 or rgb.shape[-1] != 3 or depth.shape != rgb.shape[:2]:
        raise ValueError("rgb/depth geometry mismatch")
    if density < 0 or max_amount < 0 or max_amount > 1:
        raise ValueError("invalid atmosphere parameters")
    finite_depth = np.where(np.isfinite(depth), depth, 65504.0).astype(np.float32)
    amount = 1.0 - np.exp(-np.float32(density) * np.maximum(finite_depth - np.float32(near), 0.0))
    amount = np.clip(amount, 0.0, np.float32(max_amount)).astype(np.float32)
    haze = np.asarray(color, dtype=np.float32)
    if haze.shape != (3,):
        raise ValueError("atmosphere color must be RGB")
    return rgb * (1.0 - amount[..., None]) + haze[None, None, :] * amount[..., None]


def emission_rebalance_rgb(rgb: np.ndarray, emission: np.ndarray, *, gain: float = 1.0) -> np.ndarray:
    if rgb.shape != emission.shape or rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ValueError("rgb/emission geometry mismatch")
    if gain < 0:
        raise ValueError("emission gain must be nonnegative")
    return np.maximum(0.0, rgb + emission * np.float32(gain - 1.0))


def selective_exposure_rgb(rgb: np.ndarray, mask: np.ndarray, *, exposure_stops: float = 0.0) -> np.ndarray:
    if rgb.ndim != 3 or rgb.shape[-1] != 3 or mask.shape != rgb.shape[:2]:
        raise ValueError("rgb/mask geometry mismatch")
    m = np.clip(mask.astype(np.float32), 0.0, 1.0)
    factor = np.float32(2.0 ** exposure_stops)
    graded = rgb * factor
    return rgb * (1.0 - m[..., None]) + graded * m[..., None]


def reinhard_srgb_rgb(rgb: np.ndarray, *, exposure_stops: float = 0.0) -> np.ndarray:
    if rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ValueError("rgb must be HxWx3")
    exposure = np.float32(2.0 ** exposure_stops)
    x = np.maximum(rgb * exposure, 0.0)
    x = x / (1.0 + x)
    cutoff = np.float32(0.0031308)
    srgb = np.where(
        x <= cutoff,
        x * np.float32(12.92),
        np.float32(1.055) * np.power(x, np.float32(1.0 / 2.4)) - np.float32(0.055),
    )
    return np.clip(srgb, 0.0, 1.0).astype(np.float32)
