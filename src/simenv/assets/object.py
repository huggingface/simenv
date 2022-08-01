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
""" A simenv Scene Object."""
import itertools
from typing import List, Optional, Union

import numpy as np
import pyvista as pv

from .asset import Asset
from .collider_component import Collider
from .material import Material
from .procgen.prims import generate_prims_maze
from .procgen.wfc import generate_2d_map, generate_map


class Object3D(Asset):
    """Create a 3D Object.

    Parameters
    ----------

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        mesh: Optional[pv.UnstructuredGrid] = None,
        material: Optional[Material] = None,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        collider: Optional[Collider] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        super().__init__(name=name, position=position, parent=parent, children=children, collider=collider, **kwargs)

        self.mesh = mesh if mesh is not None else pv.PolyData()

        # Avoid having averaging normals at shared points
        # (default pyvista behavior:https://docs.pyvista.org/api/core/_autosummary/pyvista.PolyData.compute_normals.html)
        if self.mesh is not None:
            self.mesh.compute_normals(inplace=True, cell_normals=False, split_vertices=True)

        self.material = material if material is not None else Material()

    def copy(self, with_children=True, **kwargs):
        """Copy an Object3D node in a new (returned) object.

        By default mesh and materials are copied in respectively new mesh and material.
        'share_material' and 'share_mesh' can be set to True to share mesh and/or material
        between original and copy instead of creating new one.
        """
        share_material = kwargs.get("share_material", False)
        share_mesh = kwargs.get("share_mesh", False)

        mesh_copy = None
        if self.mesh is not None:
            if share_mesh:
                mesh_copy = self.mesh
            else:
                mesh_copy = self.mesh.copy()

        material_copy = None
        if self.material is not None:
            if share_material:
                material_copy = self.material
            else:
                material_copy = self.material.copy()

        copy_name = self.name + f"_copy{self._n_copies}"

        self._n_copies += 1
        instance_copy = type(self)(name=copy_name)
        instance_copy.mesh = mesh_copy
        instance_copy.material = material_copy
        instance_copy.position = self.position
        instance_copy.rotation = self.rotation
        instance_copy.scaling = self.scaling
        instance_copy.collider = self.collider

        if with_children:
            copy_children = []
            for child in self.tree_children:
                copy_children.append(child.copy(**kwargs))
            instance_copy.tree_children = copy_children
            for child in instance_copy.tree_children:
                child._post_copy()

        return instance_copy

    def __repr__(self):
        mesh_str = ""
        if self.mesh is not None:
            mesh_str = f"Mesh(points={self.mesh.n_points}, cells={self.mesh.n_cells})"
        material_str = ""
        if self.material is not None:
            base_color_str = ", ".join(f"{val:.1f}" for val in self.material.base_color)
            material_str = f", Material('{self.material.name}', base color=[{base_color_str}])"
        return f"{self.name}: {self.__class__.__name__}({mesh_str}{material_str})"

    def plot(self, **kwargs):
        self.mesh.plot(**kwargs)


class Plane(Object3D):
    """Create a plane.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the plane in ``[x, y, z]``.
        Default to normal pointing in the ``y`` (up) direction.

    i_size : float
        Size of the plane in the i direction.

    j_size : float
        Size of the plane in the j direction.

    i_resolution : int
        Number of points on the plane in the i direction.

    j_resolution : int
        Number of points on the plane in the j direction.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        i_size: Optional[float] = 10,
        j_size: Optional[float] = 10,
        i_resolution: Optional[int] = 1,
        j_resolution: Optional[int] = 1,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if direction is None:
            direction = (0, -1, 0)
        mesh = pv.Plane(
            direction=direction,
            i_size=i_size,
            j_size=j_size,
            i_resolution=i_resolution,
            j_resolution=j_resolution,
        )
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Sphere(Object3D):
    """Create a Sphere

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the top of the sphere points to in ``[x, y, z]``.
        Default to top of sphere pointing in the ``y`` (up) direction.

    radius : float, optional
        Sphere radius.

    theta_resolution : int , optional
        Set the number of points in the longitude direction (ranging
        from ``start_theta`` to ``end_theta``).

    phi_resolution : int, optional
        Set the number of points in the latitude direction (ranging from
        ``start_phi`` to ``end_phi``).

    start_theta : float, optional
        Starting longitude angle.

    end_theta : float, optional
        Ending longitude angle.

    start_phi : float, optional
        Starting latitude angle.

    end_phi : float, optional
        Ending latitude angle.

    sphere_type : str, optional
        One of 'uv' for a UV-sphere or 'ico' for an icosphere.
    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        collider: Optional[Collider] = None,
        radius: Optional[float] = 1.0,
        theta_resolution: Optional[int] = 10,
        phi_resolution: Optional[int] = 10,
        start_theta: Optional[float] = 0,
        end_theta: Optional[float] = 360,
        start_phi: Optional[float] = 0,
        end_phi: Optional[float] = 180,
        sphere_type: Optional[str] = "uv",
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if sphere_type not in ["uv", "ico"]:
            raise ValueError("Sphere type should be one of 'uv' or 'ico'.")

        from vtkmodules.vtkFiltersSources import vtkSphereSource

        sphere = vtkSphereSource()
        sphere.SetRadius(radius)
        sphere.SetThetaResolution(theta_resolution)
        sphere.SetPhiResolution(phi_resolution)
        sphere.SetStartTheta(start_theta)
        sphere.SetEndTheta(end_theta)
        sphere.SetStartPhi(start_phi)
        sphere.SetEndPhi(end_phi)
        sphere.SetLatLongTessellation(bool(sphere_type == "uv"))
        sphere.Update()
        mesh = pv.wrap(sphere.GetOutput())
        mesh.rotate_y(-90, inplace=True)
        if direction is None:
            direction = (0, 1, 0)
        pv.translate(mesh, (0, 0, 0), direction)

        if collider is None:
            collider = Collider(
                type="sphere",
                bounding_box=(radius, radius, radius),
            )

        super().__init__(
            name=name, mesh=mesh, position=position, parent=parent, children=children, collider=collider, **kwargs
        )


# TODO: add rest of arguments
class Capsule(Object3D):
    """
    A capsule (a cylinder with hemispheric ends).

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the capsule points to in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    height : float
      Center to center distance of two spheres

    radius : float
      Radius of the cylinder and hemispheres

    radius : float, optional
        Sphere radius.

    theta_resolution : int , optional
        Set the number of points in the longitude direction (ranging
        from ``start_theta`` to ``end_theta``).

    phi_resolution : int, optional
        Set the number of points in the latitude direction (ranging from
        ``start_phi`` to ``end_phi``).

    sphere_type : str, optional
        One of 'uv' for a UV-sphere or 'ico' for an icosphere.

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        collider: Optional[Collider] = None,
        height: Optional[float] = 1.0,
        radius: Optional[float] = 0.2,
        theta_resolution: Optional[int] = 4,
        phi_resolution: Optional[int] = 4,
        sphere_type: Optional[str] = "uv",
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if sphere_type not in ["uv", "ico"]:
            raise ValueError("Sphere type should be one of 'uv' or 'ico'.")

        from vtkmodules.vtkFiltersSources import vtkCapsuleSource

        capsule = vtkCapsuleSource()  # TODO pyvista capsules are aranged on the side
        capsule.SetRadius(radius)
        capsule.SetCylinderLength(max(0, height - radius * 2))
        capsule.SetThetaResolution(theta_resolution)
        capsule.SetPhiResolution(phi_resolution)
        capsule.SetLatLongTessellation(bool(sphere_type == "uv"))
        capsule.Update()

        mesh = pv.wrap(capsule.GetOutput())
        mesh.rotate_z(-90, inplace=True)
        if direction is None:
            direction = (0, 1, 0)
        pv.translate(mesh, (0, 0, 0), direction)

        if collider is None:
            collider = Collider(
                type="capsule",
                bounding_box=(radius, height, radius),
            )

        super().__init__(
            mesh=mesh, name=name, position=position, parent=parent, children=children, collider=collider, **kwargs
        )


class Cylinder(Object3D):
    """Create the surface of a cylinder.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the cylinder points to in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    radius : float, optional
        Radius of the cylinder.

    height : float, optional
        Height of the cylinder.

    resolution : int, optional
        Number of points on the circular face of the cylinder.

    capping : bool, optional
        Cap cylinder ends with polygons.  Default ``True``.

    Returns
    -------

    Examples
    --------
    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        height: Optional[float] = 1.0,
        radius: Optional[float] = 1.0,
        resolution: Optional[int] = 16,
        capping: Optional[bool] = True,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if direction is None:
            direction = (0, 1, 0)
        mesh = pv.Cylinder(direction=direction, radius=radius, height=height, resolution=resolution, capping=capping)

        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Box(Object3D):
    """Create a box with solid faces for the given bounds.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the top of the box points to in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    bounds : float or List[float], optional
        Specify the bounding box of the cube as either:
        - a list of 6 floats:(xMin, xMax, yMin, yMax, zMin, zMax)
            => bounds are ``(xMin, xMax, yMin, yMax, zMin, zMax)``
        - a list of 3 floats: xSize, ySize, zSize
            => bounds are ``(-xSize/2, xSize/2, ySize/2, ySize/2, -zSize/2, zSize/2)``
        - a single float: size
            => bounds are ``(-size/2, size/2, size/2, size/2, -size/2, size/2)``
        If no value is provide, create a centered unit box

    level : int, optional
        Level of subdivision of the faces.

    quads : bool, optional
        Flag to tell the source to generate either a quad or two
        triangle for a set of four points.  Default ``True``.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        bounds: Optional[Union[float, List[float]]] = None,
        level: Optional[int] = 0,
        quads: Optional[bool] = True,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        collider: Optional[Collider] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if bounds is None:
            bounds = (-0.5, 0.5, -0.5, 0.5, -0.5, 0.5)
        if isinstance(bounds, (float, int)):
            bounds = (-bounds / 2, bounds / 2, -bounds / 2, bounds / 2, -bounds / 2, bounds / 2)  # Make it a tuple
        if len(bounds) == 3:
            bounds = (
                -bounds[0] / 2,
                bounds[0] / 2,
                -bounds[1] / 2,
                bounds[1] / 2,
                -bounds[2] / 2,
                bounds[2] / 2,
            )  # Make it a tuple

        mesh = pv.Box(bounds=bounds, level=level, quads=quads)
        if direction is not None:
            pv.translate(mesh, (0, 0, 0), direction)

        if collider is None:
            bounding_box = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
            offset = (
                (bounds[0] + bounds[1]) / 2.0,
                (bounds[2] + bounds[3]) / 2.0,
                (bounds[4] + bounds[5]) / 2.0,
            )
            collider = Collider(type="box", bounding_box=bounding_box, offset=offset)

        super().__init__(
            mesh=mesh, name=name, position=position, parent=parent, children=children, collider=collider, **kwargs
        )


class Cone(Object3D):
    """Create a cone.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the top of the cone points to in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    height : float, optional
        Height along the cone in its specified direction.

    radius : float, optional
        Base radius of the cone.

    resolution : int, optional
        Number of facets used to represent the cone.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        height: Optional[float] = 1.0,
        radius: Optional[float] = 1.0,
        resolution: Optional[int] = 6,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if direction is None:
            direction = (0, 1, 0)
        mesh = pv.Cone(direction=direction, height=height, radius=radius, resolution=resolution)
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Line(Object3D):
    """Create a line.

    Parameters
    ----------
    pointa : np.ndarray or list, optional
        Location in ``[x, y, z]``.

    pointb : np.ndarray or list, optional
        Location in ``[x, y, z]``.

    resolution : int, optional
        Number of pieces to divide line into.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        pointa: Optional[List[float]] = None,
        pointb: Optional[List[float]] = None,
        resolution: Optional[int] = 1,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if pointa is None:
            pointa = [-1.0, 0.0, 0.0]
        if pointb is None:
            pointb = [1.0, 0.0, 0.0]
        mesh = pv.Line(pointa=pointa, pointb=pointb, resolution=resolution)

        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class MultipleLines(Object3D):
    """Create multiple lines.

    Parameters
    ----------
    points : np.ndarray or list, optional
        List of points defining a broken line, default is ``[[-0.5, 0.0, 0.0], [0.5, 0.0, 0.0]]``.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        points: Optional[List[List[float]]] = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if points is None:
            points = [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
        mesh = pv.MultipleLines(points=points)

        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class Tube(Object3D):
    """Create a tube that goes from point A to point B.

    Parameters
    ----------
    pointa : np.ndarray or list, optional
        Location in ``[x, y, z]``.

    pointb : np.ndarray or list, optional
        Location in ``[x, y, z]``.

    resolution : int, optional
        Number of pieces to divide tube into.

    radius : float, optional
        Minimum tube radius (minimum because the tube radius may vary).

    n_sides : int, optional
        Number of sides for the tube.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        pointa: Optional[List[float]] = None,
        pointb: Optional[List[float]] = None,
        resolution: Optional[int] = 1,
        radius: Optional[float] = 1.0,
        n_sides: Optional[int] = 16,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if pointa is None:
            pointa = [-1.0, 0.0, 0.0]
        if pointb is None:
            pointb = [1.0, 0.0, 0.0]
        mesh = pv.Tube(pointa=pointa, pointb=pointb, radius=radius, resolution=resolution, n_sides=n_sides)
        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class Polygon(Object3D):
    """Create a polygon.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the polygon in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    points : np.ndarray or list
        List of points defining the polygon,
            e.g. ``[[0, 0, 0], [1, 0, -.1], [.8, 0, .5], [1, 0, 1], [.6, 0, 1.2], [0, 0, .8]]``.
        The polygon is defined by an ordered list of three or more points lying in a plane.
        The polygon normal is implicitly defined by a counterclockwise ordering of
        its points using the right-hand rule.

    Returns
    -------

    Examples
    --------


    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        points: List[List[float]],
        position: Optional[List[float]] = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkPolygon

        # Setup points
        num_pts = len(points)
        v_points = pv.vtk_points(points)

        # Create the polygon
        polygon = vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(num_pts)
        for i in range(num_pts):
            polygon.GetPointIds().SetId(i, i)

        # Add the polygon to a list of polygons
        polygons = vtkCellArray()
        polygons.InsertNextCell(polygon)

        # Create a PolyData
        polygonPolyData = vtkPolyData()
        polygonPolyData.SetPoints(v_points)
        polygonPolyData.SetPolys(polygons)

        mesh = pv.PolyData(polygonPolyData)
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class RegularPolygon(Object3D):
    """Create a regular polygon.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the polygon in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    points : float, optional
        The radius of the polygon.

    n_sides : int, optional
        Number of sides of the polygon.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        radius: Optional[float] = 1.0,
        n_sides: Optional[int] = 6,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if direction is None:
            direction = (0, 1, 0)
        mesh = pv.Polygon(radius=radius, normal=direction, n_sides=n_sides)
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Ring(Object3D):
    """Create a polygonal disk with a hole in the center.

    The disk has zero height. The user can specify the inner and outer
    radius of the disk, and the radial and circumferential resolution
    of the polygonal representation.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the disc in ``[x, y, z]``.
        Default to pointing in the ``y`` (up) direction.

    inner : float, optional
        The inner radius.

    outer : float, optional
        The outer radius.

    r_res : int, optional
        Number of points in radial direction.

    c_res : int, optional
        Number of points in circumferential direction.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    # TODO(thomas) add back center and normal and see how to handle that for 2D/3D stuff
    def __init__(
        self,
        inner: Optional[float] = 0.25,
        outer: Optional[float] = 0.5,
        r_res: Optional[int] = 1,
        c_res: Optional[int] = 6,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if direction is None:
            direction = (0, 1, 0)
        mesh = pv.Disc(inner=inner, outer=outer, normal=direction, r_res=r_res, c_res=c_res)
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Text3D(Object3D):
    """Create 3D text from a string.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the disc in ``[x, y, z]``.
        Default to pointing in the ``z`` direction.

    string : str
        String to generate 3D text from.

    depth : float, optional
        Depth of the text.  Defaults to ``0.5``.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        string: Optional[str] = "Hello",
        depth: Optional[float] = 0.5,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        mesh = pv.Text3D(string=string, depth=depth)
        mesh.rotate_y(-90, inplace=True)
        if direction is None:
            direction = (0, 0, -1)
        pv.translate(mesh, (0, 0, 0), direction)

        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class Triangle(Object3D):
    """Create a triangle defined by 3 points.

    Parameters
    ----------
    points : sequence, optional
        Points of the triangle.  Defaults to a right isosceles
        triangle (see example).

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        points: Optional[List[List[float]]] = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        mesh = pv.Triangle(points=points)
        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class Rectangle(Object3D):
    """Create a rectangle defined by 4 points.

    Parameters
    ----------
    points : sequence, optional
        Points of the rectangle.  Defaults to a simple example.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        points: Optional[List[List[float]]] = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        mesh = pv.Rectangle(points=points)
        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class Circle(Object3D):
    """Create a single PolyData circle defined by radius in the XY plane.

    Parameters
    ----------
    position : np.ndarray or list, optional
        Center in ``[x, y, z]``.
        Default to a center at the origin ``[0, 0, 0]``.

    direction : list or tuple or np.ndarray, optional
        Direction the normal to the circle in ``[x, y, z]``.
        Default to pointing in the ``y`` direction.

    radius : float, optional
        Radius of circle.

    resolution : int, optional
        Number of points on the circle.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        radius: Optional[float] = 0.5,
        resolution: Optional[int] = 100,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
        direction: Optional[List[float]] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        mesh = pv.Circle(radius=radius, resolution=resolution)
        mesh.rotate_y(-90, inplace=True)
        if direction is None:
            direction = (0, 1, 0)
        pv.translate(mesh, (0, 0, 0), direction)
        super().__init__(mesh=mesh, name=name, position=position, parent=parent, children=children, **kwargs)


class StructuredGrid(Object3D):
    """Create a 3D grid (structured plane) defined by lists of X, Y and Z positions of points.

    Parameters
    ----------
    x : np.ndarray or python list of list of floats
        Position of the points in x direction.

    y : np.ndarray or python list of list of floats
        Position of the points in y direction.

    z : np.ndarray or python list of list of floats
        Position of the points in z direction.

    Returns
    -------

    Examples
    --------

    # create a 5x5 mesh grid
    xrng = np.arange(-2, 3, dtype=np.float32)
    zrng = np.arange(-2, 3, dtype=np.float32)
    x, z = np.meshgrid(xrng, zrng)
    # let's make the y axis a sort of cone
    y = 1. / np.sqrt(x*x + z*z + 0.1)
    asset = sm.StructuredGrid(x, y, z)

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        x: Union[np.ndarray, List[List[float]]],
        y: Union[np.ndarray, List[List[float]]],
        z: Union[np.ndarray, List[List[float]]],
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        if not isinstance(x, np.ndarray):
            x = np.array(x)
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        if not isinstance(z, np.ndarray):
            z = np.array(z)

        # If it is a structured grid, extract the surface mesh (PolyData)
        mesh = pv.StructuredGrid(x, y, z).extract_surface()
        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class ProcgenGrid(Object3D):
    """Create a procedural generated 3D grid (structured plane) from
        tiles / previous map.

    Parameters
    ----------
    sample_map : np.ndarray or python list of list of floats
        Map to procedurally generate from.

    specific_map: np.ndarray or python list of list of floats
        Map to procedurally generate from.

    tiles : list of tiles
        Tiles for procedural generation when using generation from tiles and neighbors definitions.
        Tiles must be NxN np.ndarray that define height maps. In the future, we plan to support
        more generic tiles.

    neighbors: list of available neighbors for each tile
        Expects pair of tiles.

    symmetries: list of char
        Expects a list of symmetry definitions. If passed, you must define a symmetry for each tile.
        Possible symmetries are "X", "I" / "/", "T" / "L", another character, and each character defines
        the tile with the same level of symmetry as the character:
        - X: has symmetry in all ways. So it has 1 different format.
        - I / `/`: when rotated, it's different from the original tile. Has 2 different formats.
        - T / L: Has 4 different formats.
        - other characters: the algorithm supposes it has 8 different formats.

    weights: list of floats
        sampling weights for each of the tiles

    width: int
        width of the generated map

    height: int
        height of the generated map

    shallow: bool
        Indicates whether procedural generation mesh should be generated or not.
        Created for the purpose of optimizing certain environments such as XLand.

    seed: int
        Random seed used for procedural generation.

    algorithm_args: dict
        Extra arguments to be passed to the procedural generation.

    Returns
    -------

    Examples
    --------

    """

    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(
        self,
        sample_map: Union[np.ndarray, List[List[List[int]]]] = None,
        specific_map: Union[np.ndarray, List[List[List[int]]]] = None,
        tiles: Optional[List] = None,
        neighbors: Optional[List] = None,
        symmetries: Optional[List] = None,
        weights: Optional[List] = None,
        width: Optional[int] = 9,
        height: Optional[int] = 9,
        shallow: Optional[bool] = False,
        algorithm_args: Optional[dict] = None,
        seed: int = None,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):

        if seed is None:
            seed = np.random.randint(0, 100000)
            print("Seed:", seed)

        # Seeding
        np.random.seed(seed)

        if sample_map is not None and not isinstance(sample_map, np.ndarray):
            sample_map = np.array(sample_map)

        if specific_map is not None and not isinstance(specific_map, np.ndarray):
            specific_map = np.array(specific_map)

        if algorithm_args is None:
            algorithm_args = {}

        # Handle when user doesn't pass arguments properly
        if (tiles is None or neighbors is None) and sample_map is None and specific_map is None:
            raise ValueError("Insert tiles / neighbors or a map to sample from.")

        # Get coordinates and image from procedural generation
        all_args = {
            "width": width,
            "height": height,
            "sample_map": sample_map,
            "tiles": tiles,
            "neighbors": neighbors,
            "weights": weights,
            "symmetries": symmetries,
            **algorithm_args,
        }

        if shallow:
            if specific_map is None:
                map_2ds = generate_2d_map(**all_args)
                # We take the first map (if nb_samples > 1), since this object has
                # support for a single map for now
                self.map_2d = map_2ds[0]

            else:
                self.map_2d = specific_map

        else:
            # Saves these for other functions that might use them
            # We take index 0 since generate_map is now vectorized, but we don't have
            # support for multiple maps on this object yet.
            coordinates, map_2ds = generate_map(specific_map=specific_map, **all_args)
            self.coordinates, self.map_2d = coordinates[0], map_2ds[0]

            # If it is a structured grid, extract the surface mesh (PolyData)
            mesh = pv.StructuredGrid(*self.coordinates).extract_surface()
            super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)

    def generate_3D(
        self,
        name: Optional[str] = None,
        parent: Optional[Asset] = None,
        children: Optional[List[Asset]] = None,
        **kwargs,
    ):
        """
        Function for creating the mesh in case the creation of map was shallow.
        """
        coordinates, _ = generate_map(specific_map=self.map_2d)
        self.coordinates = coordinates[0]

        # If it is a structured grid, extract the surface mesh (PolyData)
        mesh = pv.StructuredGrid(*self.coordinates).extract_surface()
        super().__init__(mesh=mesh, name=name, parent=parent, children=children, **kwargs)


class ProcGenPrimsMaze3D(Asset):
    __NEW_ID = itertools.count()  # Singleton to count instances of the classes for automatic naming

    def __init__(self, width: int, depth: int, name=None, wall_keep_prob=0.5, wall_material=None, **kwargs):
        self.width = width
        self.depth = depth
        self.wall_keep_prob = wall_keep_prob * 10
        if wall_material is None:
            wall_material = Material(base_color=(0.8, 0.8, 0.8))
        self.wall_material = wall_material
        if name is not None:
            self.name = name
        super().__init__(**kwargs)
        self._generate()

    def _generate(self):
        walls = generate_prims_maze((self.width, self.depth), keep_prob=self.wall_keep_prob)

        for i, wall in enumerate(walls):
            px = (wall[0] + wall[2]) / 2
            pz = (wall[1] + wall[3]) / 2
            sx = abs(wall[2] - wall[0]) + 0.1
            sz = abs(wall[3] - wall[1]) + 0.1

            self += Box(
                name=f"{self.name}_wall_{i}",
                position=[px, 0.5, pz],
                material=self.wall_material,
                scaling=[sx, 1.0, sz],
            )
