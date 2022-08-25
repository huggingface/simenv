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
"""Wrapper around SimEnv scene for easier RL training"""

import numpy as np
from gym import spaces

# Lint as: python3
from ...scene import Scene


try:
    from stable_baselines3.common.vec_env.base_vec_env import VecEnv
except ImportError:

    class VecEnv:
        pass  # Dummy class if SB3 is not installed


class ParallelRLEnvironment(VecEnv):
    def __init__(self, scene_or_map_fn, n_maps=1, n_show=1, frame_rate=30, frame_skip=4, **engine_kwargs):

        if hasattr(scene_or_map_fn, "__call__"):
            self.scene = Scene(engine="Unity", **engine_kwargs)
            self.map_roots = []
            for i in range(n_maps):
                map_root = scene_or_map_fn(i)
                self.scene += map_root
                self.map_roots.append(map_root)
        else:
            self.scene = scene_or_map_fn
            self.map_roots = [self.scene]

        self.agents = {agent.name: agent for agent in self.scene.agents}
        self.n_agents = len(self.agents)
        self.n_maps = n_maps
        self.n_show = n_show
        self.n_agents_per_map = self.n_agents // self.n_maps

        self.agent = next(iter(self.agents.values()))

        self.action_space = spaces.Discrete(self.agent.action_space.n)  # quick workaround while Thom refactors this
        self.observation_space = {
            "CameraSensor": self.agent.observation_space
        }  # quick workaround while Thom refactors this
        self.observation_space = spaces.Dict(self.observation_space)

        super(ParallelRLEnvironment, self).__init__(n_show, self.observation_space, self.action_space)

        # Don't return simulation data, since minimal/faster data will be returned by agent sensors
        # Pass maps kwarg to enable map pooling
        maps = [root.name for root in self.map_roots]
        self.scene.show(
            frame_rate=frame_rate,
            frame_skip=frame_skip,
            return_frames=False,
            return_nodes=False,
            maps=maps,
            n_show=n_show,
        )

    def step(self, action=None):
        action_dict = {}
        # TODO: adapt this to multiagent setting
        if action is None:
            for i in range(self.n_show):
                action_dict[str(i)] = int(self.action_space.sample())
        elif isinstance(action, np.int64):
            action_dict["0"] = int(action)
        else:
            for i in range(self.n_show):
                action_dict[str(i)] = int(action[i])

        event = self.scene.step(action=action_dict)

        # Extract observations, reward, and done from event data
        obs = {}
        reward = 0
        done = False
        info = {}
        if self.n_agents == 1:
            agent_data = event["agents"][self.agent.name]
            camera_obs = np.array(agent_data["frames"][self.agent.camera.name], dtype=np.uint8)
            obs[self.agent.camera.name] = camera_obs
            reward = agent_data["reward"]
            done = agent_data["done"]

        else:
            reward = []
            done = []
            info = []
            for agent_name in event["agents"].keys():
                agent = self.agents[agent_name]
                agent_data = event["agents"][agent_name]
                camera_obs = np.array(agent_data["frames"][agent.camera.name], dtype=np.uint8)
                obs[agent.camera.name] = camera_obs
                reward.append(agent_data["reward"])
                done.append(agent_data["done"])
                info.append({})

        obs = self._obs_dict_to_tensor(obs)
        reward = np.array(reward)
        done = np.array(done)
        return obs, reward, done, info

    def _obs_dict_to_tensor(self, obs_dict):
        out = []
        for val in obs_dict.values():
            out.append(val)

        if self.n_agents == 1:
            return {"CameraSensor": np.stack(out)[0]}  # quick workaround while Thom refactors this
        else:
            return {"CameraSensor": np.stack(out)}  # quick workaround while Thom refactors this

    def reset(self):
        self.scene.reset()

        # To extract observations, we do a "fake" step (no actual simulation with frame_skip=0)
        event = self.scene.step(return_frames=True, frame_skip=0)
        obs = {}
        if self.n_agents == 1:
            camera_obs = np.array(event["frames"][self.agent.camera.name], dtype=np.uint8)
            obs[self.agent.camera.name] = camera_obs
        else:
            for agent_name in event["agents"].keys():
                agent = self.agents[agent_name]
                camera_obs = np.array(event["frames"][agent.camera.name], dtype=np.uint8)
                obs[agent.camera.name] = camera_obs

        obs = self._obs_dict_to_tensor(obs)
        return obs

    def close(self):
        self.scene.close()

    def env_is_wrapped(self):
        return [False] * self.n_agents * self.n_parallel

    # required abstract methods

    def step_async(self, actions: np.ndarray) -> None:
        raise NotImplementedError()

    def env_method(self):
        raise NotImplementedError()

    def get_attr(self):
        raise NotImplementedError()

    def seed(self, value):
        # this should be done when the env is initialized
        return
        # raise NotImplementedError()

    def set_attr(self):
        raise NotImplementedError()

    def step_send(self):
        raise NotImplementedError()

    def step_wait(self):
        raise NotImplementedError()
