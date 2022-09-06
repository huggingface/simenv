import argparse

import matplotlib.pyplot as plt
import numpy as np

import simenv as sm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build_exe", default=None, type=str, required=False, help="Pre-built unity app for simenv")
    args = parser.parse_args()

    CAMERA_HEIGHT = 40
    CAMERA_WIDTH = 64

    scene = sm.Scene(engine="Unity", engine_exe=args.build_exe)

    scene += sm.LightSun(name="sun", position=[0, 20, 0], intensity=0.9)
    scene += sm.Box(name="floor", position=[0, -0.05, 0], scaling=[100, 0.1, 100])
    scene += sm.Box(name="wall1", position=[-1, 0.5, 0], scaling=[0.1, 1, 5.1])
    scene += sm.Box(name="wall2", position=[1, 0.5, 0], scaling=[0.1, 1, 5.1])
    scene += sm.Box(name="wall3", position=[0, 0.5, 4.5], scaling=[5.9, 1, 0.1])
    scene += sm.Box(name="wall4", position=[-2, 0.5, 2.5], scaling=[1.9, 1, 0.1])
    scene += sm.Box(name="wall5", position=[2, 0.5, 2.5], scaling=[1.9, 1, 0.1])
    scene += sm.Box(name="wall6", position=[-3, 0.5, 3.5], scaling=[0.1, 1, 2.1])
    scene += sm.Box(name="wall7", position=[3, 0.5, 3.5], scaling=[0.1, 1, 2.1])
    scene += sm.Box(name="wall8", position=[0, 0.5, -2.5], scaling=[1.9, 1, 0.1])

    agent = sm.SimpleActor(
        camera_width=CAMERA_WIDTH,
        camera_height=CAMERA_HEIGHT,
        position=[0.0, 0.0, 0.0],
    )

    scene += agent
    scene.show()
    plt.ion()
    fig1, ax1 = plt.subplots()
    dummy_obs = np.zeros(shape=(CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
    axim1 = ax1.imshow(dummy_obs, vmin=0, vmax=255)

    for i in range(1000):
        action = scene.action_space.sample()
        if type(action) == int:  # discrete are ints, continuous are numpy arrays
            action = action
        else:
            action = action.tolist()

        obs, reward, done, info = scene.step(action)
        axim1.set_data(obs["CameraSensor"].transpose(1, 2, 0))
        fig1.canvas.flush_events()

    scene.close()
