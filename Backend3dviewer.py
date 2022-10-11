import pymeshlab



def calculate_normals_for_point_cloud(ms : pymeshlab.MeshSet,  view_points Lower_boundaries , Upper_boundaries):

point_cloud = ms.current_mesh.vertex_matrix()
Mesh = pymeshlab.Mesh(point_cloud)
ms2 =pymeshlab.MeshSet()
ms2.add_mesh(point_cloud)

return
