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
""" A simenv Physic Material."""
from dataclasses import dataclass
from typing import Optional

from .gltf_extension import GltfExtensionMixin


@dataclass
class PhysicMaterial(GltfExtensionMixin, gltf_extension_name="HF_physic_materials"):
    """
    A physic material.

    Properties:
    dynamic_friction (number) The friction used when already moving. Usually a value from 0 to 1. (Optional, default 0.6)
    static_friction (number) The friction used when laying still on a surface. Usually a value from 0 to 1. (Optional, default 0.6)
    bounciness (number) How bouncy a surface is. 0 will not bounce, 1 will bounce without any loss of energy. (Optional, default 0)
    friction_combine (str) How the friction of two surfaces are combined. (Optional, default "average")
    bounce_combine (str) How the bounciness of two surfaces are combined. (Optional, default "average")
    """

    dynamic_friction: Optional[float] = None
    static_friction: Optional[float] = None
    bounciness: Optional[float] = None
    friction_combine: Optional[str] = None
    bounce_combine: Optional[str] = None

    def __post_init__(self):
        if self.dynamic_friction is None:
            self.dynamic_friction = 0.6
        if self.static_friction is None:
            self.static_friction = 0.6
        if self.bounciness is None:
            self.bounciness = 0.0
