import numpy as np
import pytest

from src.core.finishing_math import (
    depth_atmosphere_rgb,
    emission_rebalance_rgb,
    reinhard_srgb_rgb,
    selective_exposure_rgb,
)


def test_depth_atmosphere_increases_with_distance():
    rgb=np.ones((1,2,3),dtype=np.float32)
    depth=np.array([[1.0,100.0]],dtype=np.float32)
    out=depth_atmosphere_rgb(rgb,depth,near=0,density=.1,max_amount=.5,color=(0,0,0))
    assert np.allclose(out[0,0],np.exp(-.1),atol=1e-5)
    assert np.allclose(out[0,1],.5,atol=1e-5)


def test_depth_atmosphere_rejects_bad_geometry():
    with pytest.raises(ValueError):
        depth_atmosphere_rgb(np.zeros((2,2,3),np.float32),np.zeros((3,3),np.float32))


def test_emission_rebalance_gain_one_is_identity():
    rgb=np.full((2,2,3),.2,np.float32)
    emission=np.full_like(rgb,.5)
    assert np.array_equal(emission_rebalance_rgb(rgb,emission,gain=1),rgb)


def test_selective_exposure_only_changes_mask():
    rgb=np.ones((1,2,3),dtype=np.float32)
    mask=np.array([[1,0]],dtype=np.float32)
    out=selective_exposure_rgb(rgb,mask,exposure_stops=1)
    assert np.allclose(out[0,0],2)
    assert np.allclose(out[0,1],1)


def test_reinhard_srgb_is_bounded_and_monotonic():
    rgb=np.array([[[0,0.1,10]]],dtype=np.float32)
    out=reinhard_srgb_rgb(rgb)
    assert np.all(out>=0) and np.all(out<=1)
    assert out[0,0,0] < out[0,0,1] < out[0,0,2]
