import itertools
from typing import List, Optional

from ..asset import Asset
from ..camera import Camera
from .rl_agent_actions import DiscreteRLAgentActions, RLAgentActions
from .rl_agent_reward_function import RLAgentRewardFunction


class RL_Agent(Asset):
    dimensionality = 3
    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        color: Optional[List[float]] = None,
        height: Optional[float] = 1.5,
        move_speed: Optional[float] = 5.0,
        turn_speed: Optional[float] = 2.0,
        actions: Optional[RLAgentActions] = None,
        reward_functions: Optional[List[RLAgentRewardFunction]] = None,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None,
        camera_width: Optional[int] = None,
        camera_height: Optional[int] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        super().__init__(name=name, position=position, rotation=rotation, parent=parent, children=children)

        if color is None:
            color = [1.0, 0.0, 0.0]
        if actions is None:
            actions = DiscreteRLAgentActions.default()
        if reward_functions is None:
            reward_functions = []
        if camera_width is None:
            camera_width = 32
        if camera_height is None:
            camera_height = 32

        self.color = color
        self.height = height
        self.move_speed = move_speed
        self.turn_speed = turn_speed
        self.actions = actions
        self.reward_functions = reward_functions
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera = Camera(position=[0.0, height * 0.7, 0.0], width=camera_width, height=camera_height)
        self.add(self.camera)

    def add_reward_function(self, reward_function: RLAgentRewardFunction) -> None:
        self.reward_functions.append(reward_function)

    def copy(self):
        instance_copy = super().copy()
        instance_copy.color = self.color
        instance_copy.height = self.height
        instance_copy.move_speed = self.move_speed
        instance_copy.actions = self.actions
        instance_copy.reward_functions = self.reward_functions
        # instance_copy.camera = self.camera

        return instance_copy

    def post_copy(self):
        self.reward_functions = [rf.post_copy(self) for rf in self.reward_functions]
