import numpy as np
import pymeshlab
import polyscope as ps
import polyscope.imgui as psim


class Mesh:
    '''This class is to keep track of the Meshes in the Program'''
    def __init__(self, MeshSet, name, color, radius = 0.001, mode = 'quad'):


        self.duty = MeshSet
        self.Mesh = MeshSet.current_mesh()
        self.Mesh.set_label(name)
        self.color= color
        self.name = name
        self.__radius = radius
        self.VisibleMesh=self.register_mesh(mode)
        self.id = self.Mesh.id()



    def Update(self):
        self.VisibleMesh.remove()
        self.VisibleMesh=self.register_mesh()

    def register_mesh(self, mode='quad'):
        if self.Mesh.is_point_cloud():
            VisibleMesh=ps.register_point_cloud(self.name, self.Mesh.vertex_matrix(), color=self.color)
            if mode == 'quad':
                VisibleMesh.set_point_render_mode('quad')
            VisibleMesh.set_radius(self.__radius)
        else:
            VisibleMesh=ps.register_surface_mesh(self.name, self.Mesh.vertex_matrix(), self.Mesh.face_matrix(), color=self.color)

        return VisibleMesh

    def set_enabled(self, enabled):
        self.VisibleMesh.set_enabled(enabled)

    def set_current_mesh(self):
        self.duty.set_current_mesh(self.id)

    def __del__(self):
        self.VisibleMesh.remove()
        self.duty.set_current_mesh(self.id)
        self.duty.delete_current_mesh()
