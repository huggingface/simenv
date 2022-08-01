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
""" A simenv RigidBodyComponent."""
import itertools
from dataclasses import dataclass
from typing import ClassVar, List, Optional

from dataclasses_json import dataclass_json


ALLOWED_CONSTRAINTS = [
    "freeze_position_x",
    "freeze_position_y",
    "freeze_position_z",
    "freeze_rotation_x",
    "freeze_rotation_y",
    "freeze_rotation_z",
]


@dataclass_json
@dataclass()
class RigidBodyComponent:
    """
    A rigid body caracteristics that can be added to a primitive.

    Parameters
    ----------
    name : string, optional
        The user-defined name of this material

    mass : float
        Mass of the rigidbody

    constraints : List[str], optional
        List of constraints to apply to the rigidbody, selected in:
            [FreezePositionX, FreezePositionY, FreezePositionZ,
             FreezeRotationX, FreezeRotationY, FreezeRotationZ,
             FreezePosition, FreezeRotation, FreezeAll]

    use_gravity : bool, optional
        Whether the rigidbody should ignore gravity

    continuous : bool, optional
        Whether to use continuous collision detection, for slower
            but more precise collision detection (recommended for
            small but fast-moving objects)

    kinematic : bool, optional
        Whether to ignore force collisions and treat the rigidbody
            as kinematic. Equivalent to isKinematic in Unity
            and custom_integrator in Godot

    """

    __NEW_ID: ClassVar[int] = itertools.count()  # Singleton to count instances of the classes for automatic naming

    mass: Optional[float] = None
    center_of_mass: Optional[List[float]] = None
    inertia_tensor: Optional[List[float]] = None
    drag: Optional[float] = None  # TODO: I would maybe rename it to "linear_drag"
    angular_drag: Optional[float] = None
    constraints: Optional[List[str]] = None
    use_gravity: Optional[bool] = None
    continuous: Optional[bool] = None  # TODO: see if we want to keep this one
    kinematic: Optional[bool] = None  # TODO: see if we want to keep this one

    def __post_init__(self):
        # Setup all our default values
        if self.mass is None:
            self.mass = 1.0
        self.mass = float(self.mass)
        if self.drag is None:
            self.drag = 0.0
        self.drag = float(self.drag)
        if self.angular_drag is None:
            self.angular_drag = 0.0
        self.angular_drag = float(self.angular_drag)

        if self.constraints is None:
            self.constraints = []
        for contraint in self.constraints:
            if contraint not in ALLOWED_CONSTRAINTS:
                raise ValueError(f"Contraint {contraint} not in allowed list: {ALLOWED_CONSTRAINTS}")

        if self.use_gravity is None:
            self.use_gravity = True
        if self.continuous is None:
            self.continuous = False
        if self.kinematic is None:
            self.kinematic = False

    def __hash__(self):
        return id(self)
