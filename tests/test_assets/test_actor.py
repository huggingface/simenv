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
import unittest

import simenv as sm


# TODO add more tests on saving/exporting/loading in gltf files
class ActorTest(unittest.TestCase):
    def test_create_agent(self):
        actor = sm.EgocentricCameraActor()
        self.assertIsInstance(actor, sm.EgocentricCameraActor)
        self.assertIsInstance(actor, sm.Capsule)

        self.assertIsInstance(actor.controller, sm.Controller)
        self.assertIsInstance(actor.physics_component, sm.RigidBodyComponent)

        self.assertTrue(len(actor), 1)
        self.assertIsInstance(actor.tree_children[0], sm.Camera)
