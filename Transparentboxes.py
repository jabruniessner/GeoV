import polyscope as ps
import numpy as np
import polyscope.imgui as psim

def main():

    x_position = 0
    y_position = 0
    z_position = 0
    length_x = 2.
    length_y = 2.
    length_z = 2.
    Create_bounding_box = False

    points_bounding_box = draw_box([x_position, y_position, z_position], length_x, length_y, length_z)
    faces_bounding_box = np.array([[0, 1, 2],
                                   [0, 1, 3],
                                   [0, 2, 3],
                                   [5, 2, 4],
                                   [5, 2, 1],
                                   [5, 1 ,4],
                                   [6, 4, 3],
                                   [6, 4, 1],
                                   [6, 1, 3],
                                   [7, 4, 3],
                                   [7, 4, 2],
                                   [7, 2, 3]])

    def callback():
        nonlocal x_position
        nonlocal y_position
        nonlocal z_position
        nonlocal view_point
        nonlocal Create_bounding_box
        nonlocal bounding_box
        nonlocal points_bounding_box

        nonlocal length_x
        nonlocal length_y
        nonlocal length_z

        points_bounding_box = draw_box([x_position, y_position, z_position],length_x,length_y, length_z)

        _, Create_bounding_box = psim.Checkbox('Create bounding box', Create_bounding_box)
        _, x_position = psim.SliderFloat('x', x_position, v_min = -1, v_max = 1)
        _, y_position = psim.SliderFloat('y', y_position, v_min = -1, v_max = 1)
        _, z_position = psim.SliderFloat('z', z_position, v_min = -1, v_max = 1)

        _, length_x = psim.SliderFloat('length x', length_x, v_min = 0, v_max = 2)
        _, length_y = psim.SliderFloat('length y', length_y, v_min = 0, v_max = 2)
        _, length_z = psim.SliderFloat('length z', length_z, v_min = 0, v_max = 2)

        bounding_box.remove()
        bounding_box = ps.register_surface_mesh('bounding box',points_bounding_box, faces_bounding_box, color = (0, 0, 1), enabled=False, transparency=0.5)

        if Create_bounding_box:
            bounding_box.set_enabled(True)



        view_point.remove()
        view_point = ps.register_point_cloud('view_point', np.array([[x_position, y_position, z_position]]), radius=0.1, color=(1, 0,0))



    ps.init()
    view_point = ps.register_point_cloud('view point', np.array([[x_position, y_position, z_position]]), radius=0.1, color=(1,0,0))
    bounding_box = ps.register_surface_mesh('bounding box', points_bounding_box, faces_bounding_box, color = (0, 0, 1), enabled=False, transparency=0.5)
    origin = ps.register_point_cloud('origin', np.array([[0,0,0]]), color=(0,0,1), radius=0.1)
    ps.set_user_callback(callback)
    #ps.set_automatically_compute_scene_extents(False)
    ps.show()

def draw_box(point, a, b, c):
    x_position= point[0]
    y_position= point[1]
    z_position= point[2]

    points_bounding_box = np.array([[x_position-a/2, y_position-b/2, z_position-c/2],
                                    [x_position+a/2, y_position-b/2, z_position-c/2],
                                    [x_position-a/2, y_position+b/2, z_position-c/2],
                                    [x_position-a/2, y_position-b/2, z_position+c/2],
                                    [x_position+a/2, y_position+b/2, z_position+c/2],
                                    [x_position+a/2, y_position+b/2, z_position-c/2],
                                    [x_position+a/2, y_position-b/2, z_position+c/2],
                                    [x_position-a/2, y_position+b/2, z_position+c/2]])

    return points_bounding_box





if __name__ == '__main__':
    main()
