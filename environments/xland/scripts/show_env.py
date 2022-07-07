"""
Minimal script for generating a map, and then randomly sampling from it.
"""

import argparse
from collections import defaultdict

import numpy as np
from matplotlib import pyplot as plt
from xland import generate_env
from xland.utils import create_2d_map, generate_tiles

from simenv.rl_env import RLEnv


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Check generate_env for more information about the arguments where
    # `help`` is not provided
    parser.add_argument("--periodic_output", type=bool, default=True)
    parser.add_argument("--periodic_input", type=bool, default=True)
    parser.add_argument("--ground", type=bool, default=False)
    parser.add_argument("--show", type=bool, default=False)
    parser.add_argument("--verbose", type=bool, default=False)

    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--height", type=int, default=10)
    parser.add_argument("--n_objects", type=int, default=3)
    parser.add_argument("--n_agents", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max_height", type=int, default=6)
    parser.add_argument("--symmetry", type=int, default=1)
    parser.add_argument("--N", type=int, default=2)
    parser.add_argument("--nb_samples", type=int, default=1)

    parser.add_argument("--sample_from", type=str, default=None)
    parser.add_argument("--map", type=str, default=None)
    parser.add_argument("--engine", type=str, default=None)

    args = parser.parse_args()
    extra_args = defaultdict(lambda: None)

    if args.sample_from is None and args.map is None:
        tiles, neighbors = generate_tiles(args.max_height)
        extra_args["tiles"] = tiles
        extra_args["neighbors"] = neighbors

    else:
        name = args.map or args.sample_from
        m = create_2d_map(name)
        if args.map is not None:
            extra_args["specific_map"] = m
        else:
            extra_args["sample_map"] = m

    success, scene = generate_env(**vars(args), **extra_args)

    # If we want to show the map and we were successful
    if args.show and success:
        scene.show()

        if args.engine is not None and args.engine != "pyvista":
            plt.ion()
            fig1, ax1 = plt.subplots()
            dummy_obs = np.zeros(shape=(scene.agent_0.camera_height, scene.agent_0.camera_width, 3), dtype=np.uint8)
            axim1 = ax1.imshow(dummy_obs, vmin=0, vmax=255)

            env = RLEnv(scene)
            for i in range(1000):
                action = env.action_space.sample()
                if type(action) == int:  # discrete are ints, continuous are numpy arrays
                    action = [action]
                else:
                    action = action.tolist()

                obs, reward, done, info = env.step(action)
                # print(done, reward, info)
                axim1.set_data(obs)
                fig1.canvas.flush_events()

        input("Press Enter to continue...")
        scene.close()

    if success:
        print("Successful generation!")
    else:
        print("Failed to generate!")
