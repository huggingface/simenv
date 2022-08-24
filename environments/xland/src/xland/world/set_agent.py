"""Functions for setting the agent in the world."""

from simenv import EgocentricCameraAgent

from ..game.generation import add_dummy_generated_reward_fn
from ..game.predicates import add_collect_all_rewards, add_timeout_rewards


def create_agents(agent_pos, objects, predicate=None, rank=0, camera_height=72, camera_width=96):
    """
    Create agents in simenv.

    Args:
        agent_pos: list of positions of the agents
        objects: list of objects in the world
        predicate: goal of the agent
            If None, then we use a default task
        camera_width: width of the agent camera
        camera_height: height of the agent camera
        verbose: verbose for debugging
    """

    agents = []

    for i, pos in enumerate(agent_pos):
        agent = EgocentricCameraAgent(
            name="agent_" + str(rank) + "_" + str(i),
            position=pos,
            camera_height=camera_height,
            camera_width=camera_width,
            scaling=[0.8, 0.8, 0.8],
        )
        agents.append(agent)

    if predicate == "random":
        add_dummy_generated_reward_fn(objects, agents)

    else:
        # Defaults to task on collection of all objects.
        add_collect_all_rewards(agents, objects)

    add_timeout_rewards(agents)

    return agents
