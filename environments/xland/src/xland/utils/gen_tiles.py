"""
Generate tiles for debugging purposes, and for generating maps on the prototype.
"""

import numpy as np

from simenv import build_wfc_neighbor, build_wfc_tile


def img_from_tiles():
    """
    Transform tiles into an unique image for tile visualization.
    """
    raise NotImplementedError


def get_tile(h, orientation=0):
    """
    Returns plain tile of height h of a certain orientation.
    """
    return [[h, orientation, 0]]


def generate_tiles(max_height=6, weights=None, double_ramp=False):
    """
    Generate tiles for the procedural generation.
    NOTE: So far, we are using these values to get used to how to use the algorithm.

    Args:
        max_height: can be any integer between 1 and 256 (and it's advisable to use a power of 2, to avoid
            approximation errors).
        weights: weights for each of the levels of height. If none, defaults for a linear decay between [10, 0.2]
        double_ramp: whether double ramps should be allowed or not.

    Returns:
        tiles, neighbors
    """

    # TODO: which should be default weights?
    if weights is None:
        weights = np.exp(np.linspace(1.0, -3.0, max(6, max_height)))[:max_height]

    ramp_weights = [0.2] * max_height

    # Step for the height (which is represented by the intensity of the color)
    size = 1
    tiles = []
    neighbors = []
    plain_tile_names = [str(h) for h in range(max_height)]

    # Generate tiles
    for h in range(max_height):

        # Generate plain tile
        tile = get_tile(h)

        # Symmetry of a certain letter means that it has the sames symmetric
        # as the letter
        tiles.append(build_wfc_tile(size=size, tile=tile, name=plain_tile_names[h], symmetry="X", weight=weights[h]))
        neighbors.append(
            build_wfc_neighbor(left=plain_tile_names[h], left_or=0, right=plain_tile_names[h], right_or=0)
        )

        if h < max_height - 1:
            neighbors.append(
                build_wfc_neighbor(left=plain_tile_names[h + 1], left_or=0, right=plain_tile_names[h], right_or=0)
            )

        # If i == max_height - 1, then we don't add more ramps
        if h < max_height - 1:

            # NOTE: One improvement here is to start using the argument `symmetry` on the
            # xml file instead of hardcoding it here.
            # Generation of ramp tiles:
            # Here we only generate from bottom to top, right to left, left to right
            # and top to bottom, in this order
            for i in range(0, 2):
                for ax in range(0, 2):
                    # Ramp orientation (more details down here)
                    ramp_or = i * 2 + ax

                    tile = get_tile(h, ramp_or + 1)

                    # Save tiles
                    next_ramp_name = "{}{}".format(h + 1, ramp_or + 1)
                    ramp_name = "{}{}".format(h, ramp_or + 1)

                    tiles.append(
                        build_wfc_tile(size=size, tile=tile, name=ramp_name, symmetry="L", weight=ramp_weights[h])
                    )

                    # We add neighbors
                    # Notice that we have to add orientation
                    # The tiles are rotate clockwise as i * 2 + ax increases
                    # And we add a rotation to fix that and keep the ramps in the right place
                    neighbors.append(
                        build_wfc_neighbor(left=ramp_name, left_or=ramp_or, right=plain_tile_names[h], right_or=0)
                    )
                    neighbors.append(
                        build_wfc_neighbor(left=plain_tile_names[h + 1], left_or=0, right=ramp_name, right_or=ramp_or)
                    )

                    # Adding ramp to going upwards
                    if h < max_height - 2 and double_ramp:
                        neighbors.append(
                            build_wfc_neighbor(left=next_ramp_name, left_or=ramp_or, right=ramp_name, right_or=ramp_or)
                        )

    return tiles, neighbors
