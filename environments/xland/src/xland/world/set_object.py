"""
Main functions for setting objects on the map.
"""

from collections import defaultdict

import numpy as np

import simenv as sm

from ..utils import COLORS, OBJECTS, get_bounds, get_connected_components


def get_connectivity_graph(z):
    """
    Returns connectivity graph.

    NOTE: Here we are supposing that every ramp
    is connected from a lower level to a higher level.
    If this is something that might not happen anymore,
    we should change this function.

    TODO: Should we implement this in C++ instead? or at least vectorize it
    TODO: update this when adding diagonal tiles
    """
    edges = defaultdict(list)
    N, M, _ = z.shape
    nodes = np.arange(N * M).reshape((N, M))

    # Identify non plain tiles to remove them as a possibility
    # when placing objects
    plain_tiles = []

    for x in range(N):
        for y in range(M):

            if z[x, y, 1] == 0:
                plain_tiles.append(y + M * x)

            min_x, max_x, min_y, max_y = max(0, x - 1), min(N, x + 2), max(0, y - 1), min(M, y + 2)

            neighborhood = z[min_x:max_x, min_y:max_y]
            sub_nodes = nodes[min_x:max_x, min_y:max_y]
            non_diagonal_connections = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])[
                min_x - x + 1 : max_x - x + 1, min_y - y + 1 : max_y - y + 1
            ]

            # Going down
            going_down = z[x, y, 0] > neighborhood[:, :, 0]
            going_down = np.logical_and(going_down, non_diagonal_connections)

            # Same level tiles
            same_level = np.logical_and(z[x, y, 0] == neighborhood[:, :, 0], neighborhood[:, :, 1] == 0)
            same_level = np.logical_and(same_level, non_diagonal_connections)

            # Connection with ramp
            neigh_shp = neighborhood.shape
            going_ramp = np.zeros(neigh_shp[:-1], dtype=bool)

            # Going up from a ramp
            going_up = np.zeros(neigh_shp[:-1], dtype=bool)

            # Coordinates of the center
            center_x = int(x != 0)
            center_y = int(y != 0)

            # Now we fill the values considering that we might have corner cases:
            # 1. Taking a ramp down:
            if x < N - 1:
                idx_x = neigh_shp[0] - 1

                # Get if we going to other level
                going_ramp[idx_x, center_y] = np.logical_and(
                    z[x, y, 0] == neighborhood[idx_x, center_y, 0], neighborhood[idx_x, center_y, 1] == 1
                )

                # Get going_up as well from a ramp going down
                going_up[idx_x, center_y] = np.logical_and(
                    z[x, y, 0] + 1 == neighborhood[idx_x, center_y, 0], z[x, y, 1] == 1
                )

            # 2. Going left from a ramp
            if y < M - 1:
                idx_y = neigh_shp[1] - 1
                going_ramp[center_x, idx_y] = np.logical_and(
                    z[x, y, 0] == neighborhood[center_x, idx_y, 0], neighborhood[center_x, idx_y, 1] == 2
                )
                going_up[center_x, idx_y] = np.logical_and(
                    z[x, y, 0] + 1 == neighborhood[center_x, idx_y, 0], z[x, y, 1] == 2
                )

            # 3. Going up from a ramp
            if x > 0:
                going_ramp[0, center_y] = np.logical_and(
                    z[x, y, 0] == neighborhood[0, center_y, 0], neighborhood[0, center_y, 1] == 3
                )
                going_up[0, center_y] = np.logical_and(z[x, y, 0] + 1 == neighborhood[0, center_y, 0], z[x, y, 1] == 3)

            # 4. Going right from a ramp
            if y > 0:
                going_ramp[center_x, 0] = np.logical_and(
                    z[x, y, 0] == neighborhood[center_x, 0, 0], neighborhood[center_x, 0, 1] == 4
                )
                going_up[center_x, 0] = np.logical_and(z[x, y, 0] + 1 == neighborhood[center_x, 0, 0], z[x, y, 1] == 4)

            # Add edges
            edges[y + M * x] = np.concatenate(
                [sub_nodes[going_down], sub_nodes[going_up], sub_nodes[going_ramp], sub_nodes[same_level]]
            )

    # Transform into a numpy array
    # This array will be useful to identify where to set the objects
    plain_tiles = np.array(plain_tiles)

    return nodes, edges, plain_tiles


def get_playable_area(z):
    """
    Returns playable area.

    The algorithm used is dfs to get strongly connected components.
    Then we select the largest strongly connected component to be the "playable area".

    TODO: Getting as input the 1x1 tiles enc
    connected_components_mask = np.zeros(n_nodes, dtype=bool)
    connected_components_mask[largest_connected_component] = Trueoded in RGB.
    """

    # Get connectivity graph
    nodes, edges, plain_tiles = get_connectivity_graph(z)

    # Get connected components
    n_nodes = nodes.shape[0] * nodes.shape[1]
    connected_components = get_connected_components(n_nodes, edges)

    # Get largest connected component
    component_lens = [len(c) for c in connected_components]
    largest_connected_component = connected_components[np.argmax(component_lens)]
    total_area = len(largest_connected_component)

    # Avoid putting objects in ramps
    plain_idxs = [plain_tiles[i] in largest_connected_component for i in range(len(plain_tiles))]
    largest_connected_component = plain_tiles[plain_idxs]

    # Return indexes of the playable area and if the playable area is larger than
    # the threshold.
    return largest_connected_component, total_area / n_nodes


def get_mask_connected_components(component, final_shp):
    """
    Returns mask of connected components.
    """
    connected_components_mask = np.zeros(np.prod(final_shp), dtype=bool)
    connected_components_mask[component] = True
    return np.reshape(connected_components_mask, final_shp)


def get_distribution(playable_area, distribution="uniform"):
    """
    Get non-linear distribution of where to place objects.
    """
    if distribution == "uniform":
        int_values = playable_area.astype(float)
        return int_values / np.sum(int_values)

    else:
        raise NotImplementedError


def sample_index(n, p):
    """
    Sample index considering a matrix of probabilities.
    """
    i = np.random.choice(np.arange(p.size), p=p.ravel(), size=n, replace=False)
    return np.unravel_index(i, p.shape)


def get_object_fn(obj):
    """
    Returns classes depending on the object.
    """
    if obj == "Cube":
        return sm.Cube

    elif obj == "Cone":
        return sm.Cone

    elif obj == "Sphere":
        return sm.Sphere

    else:
        raise ValueError


def create_objects(positions, object_type=None, object_size=5):
    """
    Create objects in simenv.
    """

    extra_height = np.array([0, 0, object_size / 2])
    positions = positions + extra_height

    color_idxs = np.random.choice(np.arange(len(COLORS), dtype=int), size=len(positions))
    colors = [COLORS[idx] for idx in color_idxs]

    if object_type is not None:
        objects = [object_type] * len(positions)

    else:
        # Choose among options of objects
        obj_idxs = np.random.choice(np.arange(len(COLORS), dtype=int), size=len(positions))
        objects = [OBJECTS[idx] for idx in obj_idxs]

    return [
        get_object_fn(obj)(
            position=pos,
            material=sm.Material(base_color=color),
            **get_bounds(object_type=obj, object_size=object_size),
        )
        for pos, color, obj in zip(positions, colors, objects)
    ]


def get_object_pos(z, n_objects, threshold=None, distribution="uniform"):
    """
    Returns None if there is not a playable area.
    """

    if threshold is None:
        threshold = 0.2

    playable_nodes, area = get_playable_area(z)

    if area < threshold:
        print("Unsufficient playable area: {} when minimum is {}".format(area, threshold))
        return None, False

    # Get probabilities to where to place objects
    # TODO: add option to do the same as it's done in XLand from Deepmind
    probabilities = get_distribution(
        get_mask_connected_components(playable_nodes, final_shp=z.shape[:-1]), distribution=distribution
    )

    obj_pos = np.array(sample_index(n_objects, probabilities))

    # Return True showing that object placement was successful
    return obj_pos, True