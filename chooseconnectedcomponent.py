import faulthandler; faulthandler.enable()
import numpy as np
import pymeshlab
import polyscope as ps
import polyscope.imgui as psim
import Polymeshlabfusion
import os


class ChooseCC(Polymeshlabfusion.Mesh):
    '''This is the class responsible for choosing the connected components'''

    is_active = False
    connectedcomp = []
    ms = None
    current_cc = 1
    numberofcc = 0



    def __init__(self, Mesh, color=(0.3, 0.5, 1), mode = 'quad'):
        '''Slightly changed constructor method '''
        self.ms = pymeshlab.MeshSet()
        self.ms.add_mesh(Mesh)
        self.id = self.ms.current_mesh().id()
        self.Mesh = Mesh
        self.name = f"CC number {ChooseCC.numberofcc}"
        self.color = color
        self.VisibleMesh = self.register_mesh(mode)
        ChooseCC.connectedcomp.append(self)
        ChooseCC.numberofcc += 1



    def set_current_mesh(self):
        self.ms.set_current_mesh(self.id)



    def __del__(self):
        self.VisibleMesh.remove()
        self.ms.set_current_mesh(self.id)
        self.ms.delete_current_mesh()


    @classmethod
    def callback(cls, PolyGUI):

        if not psim.TreeNode('Choose connected component'):
            cls.remove_all()
            if PolyGUI.current_step>1:
                PolyGUI.layers[PolyGUI.current_step-1].set_enabled(True)
            return
        else:
            psim.TreePop()



        if psim.Button('Split up'):

            if not PolyGUI.ms.current_mesh().is_point_cloud():
                #ps.remove_all_structures()
                cls.is_active = True
                cls.ms = pymeshlab.MeshSet()
                m = PolyGUI.ms.current_mesh()
                cls.ms.add_mesh(m)
                cls.ms.generate_splitting_by_connected_components(delete_source_mesh=True)

                for cc in cls.ms:
                    ChooseCC(cc)
            else:
                ps.error("The current mesh is not a point cloud!")




        if cls.connectedcomp !=[]:
            cls.connectedcomp[cls.current_cc-1].set_current_mesh()

        current_step_clicked, cls.current_cc = psim.SliderInt(
                'Connected component no', 
                cls.current_cc, 
                v_min=1, 
                v_max=np.max([len(cls.connectedcomp), 1]))

        if psim.Button('This one'):
            Chosen_one = cls.connectedcomp[cls.current_cc-1]
            while len(cls.connectedcomp)>0:
                del cls.connectedcomp[0]
            cls.connectedcomp.append(Chosen_one)
            cls.current_cc = 1


            PolyGUI.ms.add_mesh(cls.connectedcomp[cls.current_cc-1].Mesh)
            PolyGUI.layers.append(Polymeshlabfusion.Mesh(PolyGUI.ms, f"Reconstructed component", (.2,.3,.4)))
            PolyGUI.current_step = len(PolyGUI.layers)
            cls.is_active = False



        cls.mainloop()

        if cls.is_active:
            cls.set_everything_disabled(PolyGUI.layers)



    @classmethod
    def set_everything_disabled(cls,structurelist):
        for structure in structurelist:
            structure.set_enabled(False)


    @classmethod
    def mainloop(cls):
        for i in range(len(cls.connectedcomp)):
            enabled = True if (i==cls.current_cc-1) else False
            cls.connectedcomp[i].set_enabled(enabled)

    @classmethod
    def remove_all(cls):
        while len(cls.connectedcomp)>0:
            del cls.connectedcomp[0]



MS = pymeshlab.MeshSet()


def callback():
    ChooseCC.callback(MS)

def main():
    MS.load_new_mesh(os.getcwd()+'/Experiment-78/Experiment-78+pointcloud.ply')
    #MS.load_new_mesh(os.getcwd()+'/step3.ply')
    ps.init()
    Original = Polymeshlabfusion.Mesh(MS, 'Super cool mesh', (0.5, 1, 0.5))
    ps.set_user_callback(lambda Mesh = MS : ChooseCC.callback(Mesh))
    ps.show()


if __name__ == '__main__':
    main()
