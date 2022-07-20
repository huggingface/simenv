# Copyright 2022 The HuggingFace Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
""" Some mapping from Discrete and Box Spaces to physics actions."""
from enum import Enum
from typing import List, Optional, Union

import numpy as np


try:
    from gym.spaces import Box as GymBox
    from gym.spaces import Discrete as GymDiscrete
except ImportError:

    class GymBox:
        pass  # Dummy class if gym is not installed

    class GymDiscrete:
        pass  # Dummy class if gym is not installed


class Physics(str, Enum):
    """Physics actions."""

    POSITION_X = "position_x"
    POSITION_Y = "position_y"
    POSITION_Z = "position_z"
    ROTATION_X = "rotation_x"
    ROTATION_Y = "rotation_y"
    ROTATION_Z = "rotation_z"
    VELOCITY_X = "velocity_x"
    VELOCITY_Y = "velocity_y"
    VELOCITY_Z = "velocity_z"
    ANGULAR_VELOCITY_X = "angular_velocity_x"
    ANGULAR_VELOCITY_Y = "angular_velocity_y"
    ANGULAR_VELOCITY_Z = "angular_velocity_z"


class MappedActions:
    """A generic action space mapped to physics engine actions"""

    pass


class MappedBox(GymBox, MappedActions):
    """A gym Box Space with a physics magnitude linearly mapped to a physics engine magnitude.

    We currently force identical bound for each dimension

        >>> MappedBox(low=-1.0, high=2.0, shape=(3, 4), dtype=np.float32)
        MappedBox(3, 4)
    """

    def __init__(
        self,
        low: Union[float, List[float]],
        high: Union[float, List[float]],
        shape: Optional[List[int]] = None,
        dtype=np.float32,
        seed: Optional[int] = None,
        physics: Physics = None,
        scaling: Optional[float] = 1.0,
        offset: Optional[float] = 0.0,
        clip_low: Optional[List[float]] = None,
        clip_high: Optional[List[float]] = None,
    ):
        if isinstance(low, float):
            low = [low]
        if isinstance(high, float):
            high = [high]
        if shape is None:
            shape = [1] * len(low)
        super().__init__(low=low, high=high, shape=shape, dtype=dtype, seed=seed)
        self.physics = physics
        self.scaling = scaling
        self.offset = offset
        self.clip_low = clip_low
        self.clip_high = clip_high


class MappedDiscrete(GymDiscrete, MappedActions):
    r"""A gym Discrete Space where each action is mapped to a physics engine action.

    A discrete space in :math:`\{ 0, 1, \\dots, n-1 \}`.

    Example::

        >>> Discrete(2)

    """

    def __init__(
        self,
        n: int,
        seed: Optional[int] = None,
        physics: List[Physics] = None,
        amplitudes: Optional[List[float]] = None,
        clip_low: Optional[List[float]] = None,
        clip_high: Optional[List[float]] = None,
    ):

        super().__init__(n=n, seed=seed)
        self.physics = physics
        self.amplitudes = amplitudes
        self.clip_low = clip_low
        self.clip_high = clip_high
