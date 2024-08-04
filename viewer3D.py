import numpy as np
import pymeshlab
import Backendstartpage
import gc
import sys
import cuttingalongsurfaces
import Polymeshlabfusion
import polyscope as ps
import polyscope.imgui as psim
import os
from tkinter import *
import Filedialog
import probecontrol
import chooseconnectedcomponent
import Askopenfolder
import dummyloadingfunction


class PolyscopeGUI:

    def __init__(self,master,file, channelnum, Name, point_cloud, view_point_x, view_point_y, view_point_z, resolutions, ranges,  faces = None):


        '''This is the 3Dviewer class'''


        self.master = master
        self.name=Name
        self.file = file
        self.channelnum = channelnum

        #creating MeshSet
        self.ms=pymeshlab.MeshSet()

        #steps:

        self.current_step = 1
        self.layers = []



        #sample number
        self.sample_number = 40000
        self.sub_sample_perc = 0.1
        self.best_sample_bool = False
        self.best_sample_pool_size = 10
        self.exact_number_of_samples = False
        self.__simplified_count = 0


        #preclean and outlier selection
        self.select_outliers = False
        self.probability = 0.5
        self.number_of_neighbours = 32
        self.preview_exist = False
        self.cleaned_count = 0

        #estimation of normals
        self.view_point_selection = True
        self.multiple_view_points = False

        self.view_point_x, self.view_point_y, self.view_point_z = view_point_x, view_point_y, view_point_z
        self.range_x= ranges[0][1]
        self.range_y= ranges[1][1]
        self.range_z= ranges[2][1]



        self.smoothiter = 0
        self.number_of_neighbours_normals = 50

        self.rescale_z_axis_bool = False

        #Reconstruction Options
        self.ReconstructionOptions=self.Reconstruction()
        self.__mesh_num = 1

        #creating a filedialogs for all cases
        self.filedialog_stack = Filedialog.Filedialog(formats = ['*.tif'], savingfunction = self.save_stack, name = "Choose File", mode = 'File')
        self.filedialog_stack_on_original = Filedialog.Filedialog(formats = ['*.tif'], savingfunction=  self.save_stack_on_original, name="Choose File", mode = 'File')
        self.filedialog_mesh = Filedialog.Filedialog(formats = ['*.ply', '*.obj', '*.stl'], savingfunction = self.save_mesh, name = "Choose File", mode = 'File')
        self.filedialog_project = Filedialog.Filedialog(formats = ["[Dir]"], savingfunction = self.save_project, name = "Choose directory", mode = 'Dir')
        self.folderdialog_load_viewpoints = Askopenfolder.Askopenfolder(formats=["[Dir]"], loadingfunction = probecontrol.ViewPoints.loadviewpoints,
                                                                        name="Choose directory", mode ='Dir')





        #Smoothing options
        self.smoothingOptions=self.Smoothing(view_point_x, view_point_y, view_point_z)



        self.GeometricMeasures_opt = self.GeometricMeasures(self.ms, self)


        self.Slicing = self.Photoslices(self.ms, resolutions, ranges)


        if faces == None:
            m = pymeshlab.Mesh(vertex_matrix = point_cloud)
        else:
            m = pymeshlab.Mesh(vertex_matrix = point_cloud, face_matrix=faces)

        self.ms.add_mesh(m)



        #self.p_mesh = ps.register_surface_mesh('my point cloud',points, faces)



        first_mesh = Polymeshlabfusion.Mesh(self.ms, 'First Mesh', (0.11, 0.388, 0.890))
        self.layers.append(first_mesh)
        del first_mesh

        #register the view point
        probecontrol.ViewPoints.probes = []
        probecontrol.ViewPoints(self.view_point_x, self.view_point_y, self.view_point_z, self.range_y, self.range_y, self.range_z)

        ps.set_user_callback(self.__callback)

        ps.show()
        probecontrol.ViewPoints.remove_all()
        self.remove_all_layers()
        ps.clear_user_callback()
        ps.remove_all_structures()




    def __callback(self):
        '''This function is responsible for defining the actual GUI'''
        if self.layers != []:
            self.layers[self.current_step-1].set_current_mesh()



        if(psim.TreeNode('Steps')):
            current_step_clicked, self.current_step = psim.SliderInt('Mesh no', self.current_step, v_min=1, v_max=len(self.layers))
            if(psim.Button('Delete current mesh') and self.current_step > 0):
                if self.layers != []:
                    print(sys.getrefcount(self.layers[0]))
                    del self.layers[self.current_step-1]
                    self.current_step=self.current_step-1






        if(psim.TreeNode('Point cloud simplification')):
            psim.PushItemWidth(67)
            sample_number_clicked, self.sample_number = psim.InputInt('Number of samples', self.sample_number)
            psim.PopItemWidth()
            psim.SameLine()
            psim.PushItemWidth(60)
            percentage_clicked, self.sub_sample_perc = psim.InputFloat('% in World Unit', self.sub_sample_perc)
            psim.PopItemWidth()
            best_sample_heuristic, self.best_sample_bool = psim.Checkbox('Best sample heuristic', self.best_sample_bool)
            psim.SameLine()
            psim.PushItemWidth(60)
            best_sampe_pool_size, self.best_sample_pool_size = psim.InputInt('Best sample Pool size', self.best_sample_pool_size)
            psim.PopItemWidth()
            exact_number_of_samples, self.exact_number_of_samples = psim.Checkbox('Exact number of samples', self.exact_number_of_samples)
            psim.SameLine()
            if(psim.Button("Simplify")):
                self.layers[self.current_step-1].set_current_mesh()
                self.ms.generate_simplified_point_cloud(samplenum=self.sample_number, radius=pymeshlab.PercentageValue(self.sub_sample_perc),
                                                            bestsampleflag = self.best_sample_bool, bestsamplepool=self.best_sample_pool_size, exactnumflag = self.exact_number_of_samples)
                self.__simplified_count += 1
                self.layers.append(Polymeshlabfusion.Mesh(self.ms, f"simplified cloud {self.__simplified_count}", (.2,.7,.2)))


                #proceed to the next step
                self.current_step = len(self.layers)




        if(psim.TreeNode('Preclean Options')):
            psim.TextUnformatted("Would you like to select outliers?")

            psim.PushItemWidth(150)
            probability_slider, self.probability = psim.SliderFloat("Probability", self.probability,
                                                      v_min=0, v_max=1)
            psim.PopItemWidth()

            psim.SameLine()

            psim.PushItemWidth(100)
            neighbour_num, self.number_of_neighbours = psim.InputInt('Number of neighbours', self.number_of_neighbours, step = 1)
            psim.PopItemWidth()


            if(psim.Button('Show Preview')):
                self.ms.set_selection_none()
                self.layers[self.current_step-1].set_current_mesh()
                color = self.layers[self.current_step-1].color
                self.ms.compute_selection_point_cloud_outliers(propthreshold=self.probability, knearest = self.number_of_neighbours)
                current_vertices = self.ms.current_mesh()
                vertex_bool = current_vertices.vertex_selection_array()
                self.color_map = self.colorize_the_selected_points(vertex_bool, np.array(color), np.array([1,0,0]))
                self.layers[self.current_step-1].VisibleMesh.add_color_quantity('selected', self.color_map, enabled=True)
                self.preview_exist = True


            psim.SameLine()

            if(psim.Button('Apply')):
                if not self.preview_exist:
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.set_selection_none()
                    self.ms.compute_selection_point_cloud_outliers(propthreshold=self.probability, knearest = self.number_of_neighbours)


                self.ms.generate_copy_of_current_mesh()
                self.cleaned_count+=1
                self.ms.meshing_remove_selected_vertices()
                self.layers.append(Polymeshlabfusion.Mesh(self.ms, f"cleaned {self.cleaned_count}", (.7,.2,.2)))
                self.current_step = len(self.layers)




        if(psim.TreeNode('Calculate normals')):
            with_view_point, self.view_point_selection = psim.Checkbox('Orientation of normals with respect to view point', self.view_point_selection)
            with_multiple, self.multiple_view_points = psim.Checkbox('Multiple view points', self.multiple_view_points)

            if with_multiple and not self.multiple_view_points:
                probecontrol.ViewPoints.probes = [probecontrol.ViewPoints.probes[0]]

            if self.multiple_view_points:
                self.view_point_selection = True
                probecontrol.ViewPoints.probes[0].Create_bounding_box = True

                if(psim.Button('Add view point')):
                    probecontrol.ViewPoints(self.view_point_x, self.view_point_y, self.view_point_z, self.range_y, self.range_y, self.range_z, Create_bounding_box=True)

            else:
                probecontrol.ViewPoints.probes[0].Create_bounding_box = False



            probecontrol.ViewPoints.callback()


            psim.PushItemWidth(100)
            smoothiter_select, self.smoothiter= psim.InputInt('Smoothiterations', self.smoothiter, step = 1)
            psim.PopItemWidth()

            psim.SameLine()

            psim.PushItemWidth(100)
            number_of_neighbours_normals_selected, self.number_of_neighbours_normals= psim.InputInt('Number of neighbours', self.number_of_neighbours_normals, step = 1)
            psim.PopItemWidth()


            #Defining the normals calculation procedure
            if(psim.Button('Calculate Normals')):
                if not self.multiple_view_points:
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.compute_normal_for_point_clouds(k = self.number_of_neighbours_normals, smoothiter = self.smoothiter, flipflag = self.view_point_selection,
                                                                viewpos=[self.view_point_x, self.view_point_y, self.view_point_z])
                    normals = self.ms.current_mesh().vertex_normal_matrix()
                    self.layers[self.current_step-1].VisibleMesh.add_vector_quantity("normals", normals, radius=0.001, length=0.01, enabled=True)

                elif self.multiple_view_points:
                    points, normals = probecontrol.ViewPoints.calculate_normals(self.ms)
                    m = pymeshlab.Mesh(vertex_matrix=points, v_normals_matrix = normals)
                    self.ms.add_mesh(m)
                    self.layers.append(Polymeshlabfusion.Mesh(self.ms, f"cloud with normals", (.7,.2,.2)))
                    self.current_step = len(self.layers)
                    self.layers[self.current_step-1].VisibleMesh.add_vector_quantity("normals", normals, radius=0.001, length=0.01, enabled=True)

            psim.SameLine()
            if(psim.Button('Delete View Point')):
                probecontrol.ViewPoints.delete_active_view_points()


            if(psim.Button('Save view points to File')):
                probecontrol.ViewPoints.saveviewpointstofile()

            psim.SameLine()
            if(psim.Button('Load view points')):
                self.folderdialog_load_viewpoints.set_active(True)
                self.multiple_view_points = True






        if(psim.TreeNode('Reconstruction Options')):

            psim.PushItemWidth(200)
            changed = psim.BeginCombo("Pick one", self.ReconstructionOptions.ReconstructionOptions_selected)
            if changed:
                for val in self.ReconstructionOptions.ReconstructionOptions:
                    _, selected = psim.Selectable(val, self.ReconstructionOptions.ReconstructionOptions_selected==val)
                    if selected:
                        self.ReconstructionOptions.ReconstructionOptions_selected= val
                psim.EndCombo()
            psim.PopItemWidth()

            #["Screened Poisson", "APSS marching cubes", "Ball Pivoting", "VCG"]

            if self.ReconstructionOptions.ReconstructionOptions_selected == "Screened Poisson":
                self.ReconstructionOptions.screened_poisson()
                if(psim.Button('Apply')):
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.compute_selection_by_condition_per_vertex(condselect='(nx==0.0) && (ny==0.0) && (nz==0.0)')
                    self.ms.meshing_remove_selected_vertices()
                    print(f"We used {self.ms.current_mesh().vertex_number()} vertices")


                    self.ms.generate_surface_reconstruction_screened_poisson(visiblelayer=False, depth=self.ReconstructionOptions.Reconstruction_screened_poisson["Reconstruction Depth"],
                                                                                fulldepth = self.ReconstructionOptions.Reconstruction_screened_poisson["Adaptive Octree"],
                                                                                cgdepth = self.ReconstructionOptions.Reconstruction_screened_poisson["Conjugate Gradients" ],
                                                                                scale = self.ReconstructionOptions.Reconstruction_screened_poisson["Scale Factor"],
                                                                                samplespernode = self.ReconstructionOptions.Reconstruction_screened_poisson["Minimum number of samples"],
                                                                                pointweight = self.ReconstructionOptions.Reconstruction_screened_poisson["Interpolation Weight"],
                                                                                iters = self.ReconstructionOptions.Reconstruction_screened_poisson["Gauss-Seidel-Relaxation"],
                                                                                confidence =  self.ReconstructionOptions.Reconstruction_screened_poisson["Confidence Flag" ],
                                                                                preclean = self.ReconstructionOptions.Reconstruction_screened_poisson["Pre-Clean"])


                    self.__mesh_num +=1
                    self.layers.append(Polymeshlabfusion.Mesh( self.ms,f"reconstructed{self.__mesh_num}", color=(0.2, 0.2, 0.2)))
                    self.current_step=len(self.layers)



            elif self.ReconstructionOptions.ReconstructionOptions_selected == "APSS marching cubes":
                self.ReconstructionOptions.APSS_marching_cubes()
                if(psim.Button('Apply')):
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.generate_marching_cubes_apss(filterscale=self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["MLS-Filter Scale" ],
                                                projectionaccuracy = self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["Projection Accuracy (adv)"] ,
                                                maxprojectioniters = self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["Projection- Max iterations(adv)"],
                                                sphericalparameter = self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["MLS-spherical parameter"],
                                                accuratenormal = self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["Accurate Normals"],
                                                resolution = self.ReconstructionOptions.Reconstruction_APSS_marching_cubes["Grid Resolution"])

                    self.__mesh_num +=1
                    self.layers.append(Polymeshlabfusion.Mesh(self.ms,f"reconstructed{self.__mesh_num}", color=(0.2, 0.2, 0.2)))
                    self.current_step=len(self.layers)


            elif self.ReconstructionOptions.ReconstructionOptions_selected == "Ball Pivoting":
                self.ReconstructionOptions.Ball_pivoting()
                if(psim.Button('Apply')):
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.generate_surface_reconstruction_ball_pivoting(ballradius = pymeshlab.PercentageValue(self.ReconstructionOptions.Reconstruction_Ball_Pivoting["Pivoting Ball Radius"]),
                                                                    clustering = self.ReconstructionOptions.Reconstruction_Ball_Pivoting["Clustering Radius" ],
                                                                    creasethr = self.ReconstructionOptions.Reconstruction_Ball_Pivoting["Angle threshold"],
                                                                    deletefaces = self.ReconstructionOptions.Reconstruction_Ball_Pivoting["Delete original set of faces"])
                    self.__mesh_num +=1
                    self.layers.append(Polymeshlabfusion.Mesh( self.ms,f"reconstructed{self.__mesh_num}", color=(0.2, 0.2, 0.2)))
                    self.current_step=len(self.layers)


            elif self.ReconstructionOptions.ReconstructionOptions_selected == "VCG":
                self.ReconstructionOptions.VCG()
                if(psim.Button('Apply')):
                    self.layers[self.current_step-1].set_current_mesh()
                    self.ms.generate_surface_reconstruction_vcg(voxsize = pymeshlab.PercentageValue(self.ReconstructionOptions.Reconstruction_VCG["Voxel size"]),
                                                                subdiv = self.ReconstructionOptions.Reconstruction_VCG["SubVol Splitting"],
                                                                geodesic = self.ReconstructionOptions.Reconstruction_VCG["Geodesic Weighting"],
                                                                openresult = self.ReconstructionOptions.Reconstruction_VCG["Show Result"],
                                                                smoothnum = self.ReconstructionOptions.Reconstruction_VCG["Volume Laplacian Iter"],
                                                                widenum = self.ReconstructionOptions.Reconstruction_VCG["Widening"],
                                                                mergecolor = self.ReconstructionOptions.Reconstruction_VCG["Vertex Splatting"],
                                                                simplification = self.ReconstructionOptions.Reconstruction_VCG["Post Merge Simplification"],
                                                                normalsmooth = self.ReconstructionOptions.Reconstruction_VCG["Presmooth iter"])

                    self.__mesh_num +=1
                    self.layers.append(Polymeshlabfusion.Mesh( self.ms,f"reconstructed{self.__mesh_num}", color=(0.2, 0.2, 0.2)))
                    self.current_step=len(self.layers)


        chooseconnectedcomponent.ChooseCC.callback(self)



        if(psim.TreeNode('Smoothing Options')):
            #["Depth Smooth", "HC Laplacian Smooth", "Laplacian Smooth", "Laplacian Smooth (surface preserving)","Scale Dependent Laplacian Smooth", "Taubin Smooth", "Two Step Smooth"]
            psim.PushItemWidth(200)
            changed = psim.BeginCombo("Pick one", self.smoothingOptions.SmoothingOptions_Selected)
            if changed:
                for val in self.smoothingOptions.SmoothingOptions:
                    _, selected = psim.Selectable(val, self.smoothingOptions.SmoothingOptions_Selected==val)
                    if selected:
                        self.smoothingOptions.SmoothingOptions_Selected= val
                psim.EndCombo()
            psim.PopItemWidth()


            if self.smoothingOptions.SmoothingOptions_Selected == "Depth Smooth":
                self.smoothingOptions.Depth_smooth()
                if(psim.Button('Apply')):
                    self.ms.set_selection_none()
                    self.ms.apply_coord_depth_smoothing(stepsmoothnum =self.smoothingOptions.DepthSmooth["Smoothing steps"],
                                                        viewpoint = self.smoothingOptions.DepthSmooth["view point" ],
                                                        delta=pymeshlab.PercentageValue(self.smoothingOptions.DepthSmooth["Strength"]),
                                                        selected = self.smoothingOptions.DepthSmooth["Affect only selection"])
                    self.layers[self.current_step-1].Update()



            if self.smoothingOptions.SmoothingOptions_Selected == "HC Laplacian Smooth":
                if(psim.Button("Apply")):
                    self.ms.apply_coord_hc_laplacian_smoothing()
                    self.layers[self.current_step-1].Update()



            if self.smoothingOptions.SmoothingOptions_Selected == "Laplacian Smooth":
                self.smoothingOptions.Laplacian_smooth()
                if(psim.Button("Apply")):
                    self.ms.apply_coord_laplacian_smoothing(stepsmoothnum=self.smoothingOptions.Laplace["Smoothing steps"], boundary=self.smoothingOptions.Laplace["1D Boundary Smoothing"],
                                                            cotangentweight=self.smoothingOptions.Laplace["Cotangent weighting" ], selected =self.smoothingOptions.Laplace["Affect only selection"])
                    self.layers[self.current_step-1].Update()

            if self.smoothingOptions.SmoothingOptions_Selected == "Laplacian Smooth (surface preserving)":
                self.smoothingOptions.Laplacian_smooth_surface_preserving()
                if(psim.Button("Apply")):
                    self.ms.apply_coord_laplacian_smoothing_surface_preserving(selection=self.smoothingOptions.Laplace_surf_preserv["Update section"],
                                                                                angledeg=self.smoothingOptions.Laplace_surf_preserv["Max Normal Dev"],
                                                                                iterations=self.smoothingOptions.Laplace_surf_preserv["Iterations"])
                    self.layers[self.current_step-1].Update()



            if self.smoothingOptions.SmoothingOptions_Selected == "Scale Dependent Laplacian Smooth":
                self.smoothingOptions.Scale_dependant_Laplacian_smooth()

                if(psim.Button('Apply')):
                    self.ms.apply_coord_laplacian_smoothing_scale_dependent(stepsmoothnum=self.smoothingOptions.Scale_dep_Laplace["Smoothing Steps"],
                                                                            delta= pymeshlab.PercentageValue(self.smoothingOptions.Scale_dep_Laplace["delta"]),
                                                                            selected = self.smoothingOptions.Scale_dep_Laplace["Affect only selected faces"])
                    self.layers[self.current_step-1].Update()


            if self.smoothingOptions.SmoothingOptions_Selected == "Taubin Smooth":
                self.smoothingOptions.Taubin_smooth()

                if(psim.Button('Apply')):
                    self.ms.apply_coord_taubin_smoothing(lambda_ = self.smoothingOptions.Taubin["Lambda"],
                                                        mu = self.smoothingOptions.Taubin["Mu"],
                                                        stepsmoothnum = self.smoothingOptions.Taubin["Smoothing steps"],
                                                        selected = self.smoothingOptions.Taubin["Affect only selected faces"])

                    self.layers[self.current_step-1].Update()


            if self.smoothingOptions.SmoothingOptions_Selected == "Two Step Smooth":
                self.smoothingOptions.Two_step_smooth()

                if(psim.Button('Apply')):
                    self.ms.apply_coord_two_steps_smoothing(stepsmoothnum = self.smoothingOptions.Two_Step["Smoothing Steps" ],
                                                        normalthr = self.smoothingOptions.Two_Step["Feature Angle Threshold"],
                                                        stepnormalnum = self.smoothingOptions.Two_Step["Normals Smoothing Steps"],
                                                        stepfitnum = self.smoothingOptions.Two_Step["Vertex Fitting Steps"],
                                                        selected = self.smoothingOptions.Two_Step["Affect only selected faces"])

                    self.layers[self.current_step-1].Update()




        if(psim.TreeNode('Calculate Geometric Measures')):
            psim.PushItemWidth(200)
            changed = psim.BeginCombo("Pick one", self.GeometricMeasures_opt.MeasureOptions_selected)
            if changed:
                for val in self.GeometricMeasures_opt.MeasureOptions:
                    _, selected = psim.Selectable(val, self.GeometricMeasures_opt.MeasureOptions_selected==val)
                    if selected:
                        self.GeometricMeasures_opt.MeasureOptions_selected= val
                psim.EndCombo()
            psim.PopItemWidth()

            if self.GeometricMeasures_opt.MeasureOptions_selected == 'Scale dependent quadric Fitting':
                self.GeometricMeasures_opt.curvature_by_scale_dependend_quadric_fitting()
                if self.ms.current_mesh().has_vertex_scalar():
                    self.layers[self.current_step-1].VisibleMesh.add_scalar_quantity('scalar curvature', self.ms.current_mesh().vertex_scalar_array())

                if self.ms.current_mesh().has_vertex_color():
                    vc = self.ms.current_mesh().vertex_color_matrix()
                    vc = np.delete(vc, 3, 1)
                    self.layers[self.current_step-1].VisibleMesh.add_color_quantity('colorized curvature', vc)


            if self.GeometricMeasures_opt.MeasureOptions_selected == "Discrete Curvature":
                self.GeometricMeasures_opt.Discrete_Curvature()
                if self.ms.current_mesh().has_vertex_scalar():
                    self.layers[self.current_step-1].VisibleMesh.add_scalar_quantity('scalar curvature', self.ms.current_mesh().vertex_scalar_array())

                if self.ms.current_mesh().has_vertex_color():
                    vc = self.ms.current_mesh().vertex_color_matrix()
                    vc = np.delete(vc, 3, 1)
                    self.layers[self.current_step-1].VisibleMesh.add_color_quantity('colorized curvature', vc)

            if self.GeometricMeasures_opt.MeasureOptions_selected =="APSS Curvature":
                self.GeometricMeasures_opt.APSS_curvature()
                if self.ms.current_mesh().has_vertex_scalar():
                    self.layers[self.current_step-1].VisibleMesh.add_scalar_quantity('scalar curvature', self.ms.current_mesh().vertex_scalar_array())

                if self.ms.current_mesh().has_vertex_color():
                    vc = self.ms.current_mesh().vertex_color_matrix()
                    vc = np.delete(vc, 3, 1)
                    self.layers[self.current_step-1].VisibleMesh.add_color_quantity('colorized curvature', vc)

            if self.GeometricMeasures_opt.MeasureOptions_selected == 'Geodesic Distance from given point':
                self.GeometricMeasures_opt.Geod_distance_from_point()

                if self.ms.current_mesh().has_vertex_scalar():
                    self.layers[self.current_step-1].VisibleMesh.add_scalar_quantity('scalar curvature', self.ms.current_mesh().vertex_scalar_array())

                if self.ms.current_mesh().has_vertex_color():
                    vc = self.ms.current_mesh().vertex_color_matrix()
                    vc = np.delete(vc, 3, 1)
                    self.layers[self.current_step-1].VisibleMesh.add_color_quantity('colorized curvature', vc)

            if self.GeometricMeasures_opt.MeasureOptions_selected == 'Geometric Measures':
                self.GeometricMeasures_opt.Geometric_Measures()

            if self.GeometricMeasures_opt.MeasureOptions_selected == 'Topological measures':
                self.GeometricMeasures_opt.Topological_measures()

        if(psim.TreeNode('Reconstruct Photos')):
            self.Slicing.Photoslicing()

            if(psim.Button('Compute Slices')):
                mesh = self.ms.current_mesh()
                values = {'ranges': {'x': (self.Slicing.start_x, self.Slicing.end_x), 'y': (self.Slicing.start_y, self.Slicing.end_y), 'z': (self.Slicing.start_z, self.Slicing.end_z)},
                            'resolutions':{'x': self.Slicing.resolution_x, 'y': self.Slicing.resolution_y, 'z': self.Slicing.resolution_z}}
                new_mesh_vertices, self.Slicing.meshes = cuttingalongsurfaces.create_cuts(values, mesh)
                new_mesh=pymeshlab.Mesh(vertex_matrix=new_mesh_vertices)
                self.ms.add_mesh(new_mesh)
                self.__mesh_num+=1
                self.layers.append(Polymeshlabfusion.Mesh( self.ms,f"reconstructed{self.__mesh_num}", color=(0.2, 0.2, 0.2)))
                self.current_step=len(self.layers)

            psim.SameLine()

            if(psim.Button('Save stack')):
                self.filedialog_stack.set_active(True)






            psim.SameLine()
            if(psim.Button('Safe stack on top of original')):
                self.filedialog_stack_on_original.set_active(True)


        if(psim.TreeNode('Save File')):
            if(psim.Button('Save')):
                self.filedialog_mesh.set_active(True)


            if(psim.Button('Save Project')):
                self.filedialog_project.set_active(True)

        if self.folderdialog_load_viewpoints.get_active():
            self.folderdialog_load_viewpoints.askopenfile()

        if self.folderdialog_load_viewpoints.get_done():
            self.folderdialog_load_viewpoints.set_done(False)

        if self.filedialog_stack.get_active():
            self.filedialog_stack.filedialog()


        if self.filedialog_stack.get_done():
            self.filedialog_stack.set_done(False)

        if self.filedialog_stack_on_original.get_active():
            self.filedialog_stack_on_original.filedialog()

        if self.filedialog_stack_on_original.get_done():
            self.filedialog_stack_on_original.set_done(False)


        if self.filedialog_mesh.get_active():
            self.filedialog_mesh.filedialog()


        if self.filedialog_mesh.get_done():
            self.filedialog_mesh.set_done(False)

        if self.filedialog_project.get_active():
            self.filedialog_project.filedialog()


        if self.filedialog_project.get_done():
            self.filedialog_project.set_done(False)


        self.mainloop()









    def save_stack(self, file):
        images = []
        for mesh in self.Slicing.meshes:
            image = cuttingalongsurfaces.take_cross_section_photo(mesh,
                                                                    (self.Slicing.start_x, self.Slicing.end_x),
                                                                    (self.Slicing.start_y, self.Slicing.end_y),
                                                                    self.Slicing.resolution_x, self.Slicing.resolution_y)
            images.append(image)

        import tifffile
        images = np.array(images)

        try:
            tifffile.imwrite(file, images)
        except ValueError:
            pass

    def save_stack_on_original(self, file):
            if self.file[-4:]==".czi":
                import czifile
                import tifffile

                imgs = np.squeeze(czifile.CziFile(self.master.CurrentFolder+"/"+self.file).asarray())[self.channelnum]
                data_type = imgs.dtype

                images = []
                for id, mesh in enumerate(self.Slicing.meshes):
                    image = cuttingalongsurfaces.take_cross_section_photo(mesh,
                                                                            (self.Slicing.start_x, self.Slicing.end_x),
                                                                            (self.Slicing.start_y, self.Slicing.end_y),
                                                                            self.Slicing.resolution_x, self.Slicing.resolution_y)
                    image = np.transpose(image)

                    

                    new_image =  np.zeros((self.Slicing.resolution_x, self.Slicing.resolution_y), dtype = data_type)

                    indices = np.argwhere(image==255)
                    
                    for index in indices:
                        new_image[index[0], index[1]] = np.iinfo(data_type).max 
                        new_image[index[0]+1, index[1]] = np.iinfo(data_type).max 
                        new_image[index[0]-1, index[1]] = np.iinfo(data_type).max 
                        new_image[index[0], index[1]+1] = np.iinfo(data_type).max 
                        new_image[index[0], index[1]-1] = np.iinfo(data_type).max 
                        new_image[index[0]+1, index[1]+1] = np.iinfo(data_type).max 
                        new_image[index[0]+1, index[1]-1] = np.iinfo(data_type).max 
                        new_image[index[0]-1, index[1]+1] = np.iinfo(data_type).max 
                        new_image[index[0]-1, index[1]-1] = np.iinfo(data_type).max 

                

                    images.append([new_image, imgs[id], np.zeros((self.Slicing.resolution_x, self.Slicing.resolution_y), dtype = data_type)])


                images = np.array(images)
                print(images.shape)
                images = np.swapaxes(images, 1, 2)
                images = np.swapaxes(images, 2, 3)
                tifffile.imwrite(file, images)

            elif self.file[-4:]==".tif":
                import tifffile
                imgs = np.squeeze(tifffile.TiffFile(self.master.CurrentFolder+"/"+self.file).asarray())[:, self.channelnum]
                images = []
                for id, mesh in enumerate(self.Slicing.meshes):
                    image = cuttingalongsurfaces.take_cross_section_photo(mesh,
                                                                            (self.Slicing.start_x, self.Slicing.end_x),
                                                                            (self.Slicing.start_y, self.Slicing.end_y),
                                                                            self.Slicing.resolution_x, self.Slicing.resolution_y)
                    image = np.transpose(image)

                    images.append([image, imgs[id], np.zeros((self.Slicing.resolution_x, self.Slicing.resolution_y), dtype = np.uint8)])

                try:
                    images = np.array(images)
                    print(images.shape)
                    images = np.swapaxes(images, 1, 2)
                    images = np.swapaxes(images, 2, 3)
                    tifffile.imwrite(file, images)
                except ValueError:
                    print('this did not work, wron shapes!')


    def save_mesh(self, file):
        self.ms.save_current_mesh(file, binary = False)

    def save_project(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
        for id, step in enumerate(self.layers):
            self.ms.set_current_mesh(step.id)
            self.ms.save_current_mesh(folder + f"/step{id}.ply", binary = False)



    def remove_all_layers(self):
        while len(self.layers)>0:
            del self.layers[0]


    #funtion to specifiy the colores of the selected points
    def colorize_the_selected_points(self, selected, color_old, color_new):

        length = np.ones(selected.shape[0])
        color_map_old = np.tensordot(length, color_old, axes=0)
        color_map_difference = np.tensordot(selected, color_new-color_old, axes = 0)
        color_map_new = color_map_old + color_map_difference

        return color_map_new


    def mainloop(self):
        if chooseconnectedcomponent.ChooseCC.is_active:
            return

        for i in range(len(self.layers)):
            enabled = True if (i==self.current_step-1) else False
            self.layers[i].set_enabled(enabled)

    def register_new_point_cloud(self, name, color):
        m=self.ms.current_mesh()
        s=ps.register_point_cloud(name, m.vertex_matrix(), color = color)
        s.set_point_render_mode('quad')
        s.set_radius(0.001)
        self.layers.append((s, m, color))

    def register_new_mesh(self, name, color):
        m=self.ms.current_mesh()
        s=ps.register_surface_mesh(name, m.vertex_matrix(), m.face_matrix(), color=color)
        self.layers.append((s, m, color))

    def get_mesh_num(self):
        return self.__mesh_num



    class Reconstruction:
        def __init__(self):

            self.ReconstructionOptions = ["Screened Poisson", "APSS marching cubes", "Ball Pivoting", "VCG"]
            self.ReconstructionOptions_selected = self.ReconstructionOptions[0]

            self.Reconstruction_screened_poisson={"Merge all visible meshlayers": False,
                                                  "Reconstruction Depth"         :  6,
                                                  "Adaptive Octree"             :  5,
                                                  "Conjugate Gradients"         :  0,
                                                  "Scale Factor"                : 1.0,
                                                  "Minimum number of samples"   : 1.5,
                                                  "Interpolation Weight"        : 4,
                                                  "Gauss-Seidel-Relaxation"     : 8,
                                                  "Confidence Flag"            : False,
                                                  "Pre-Clean"                   : False
                                                 }

            self.Reconstruction_APSS_marching_cubes={"MLS-Filter Scale"                 :      2,
                                                     "Projection Accuracy (adv)"        : 0.0001,
                                                     "Projection- Max iterations(adv)"  :     15,
                                                     "MLS-spherical parameter"          :      1,
                                                     "Accurate Normals"                 :   True,
                                                     "Grid Resolution"                  :    200,
                                                    }

            self.Reconstruction_Ball_Pivoting={"Pivoting Ball Radius"                   :     0.0,
                                               "Clustering Radius"                      :      20,
                                               "Angle threshold"                        :      90,
                                               "Delete original set of faces"           :   False,
                                               }

            self.Reconstruction_VCG =          {"Voxel size"                            :     1.0,
                                                "SubVol Splitting"                      :       1,
                                                "Geodesic Weighting"                    :       2,
                                                "Show Result"                           :    True,
                                                "Volume Laplacian Iter"                 :       1,
                                                "Widening"                              :       3,
                                                "Vertex Splatting"                      :   False,
                                                "Post Merge Simplification"             :   False,
                                                "Presmooth iter"                        :       3
                                                }

        def screened_poisson(self):

            _, self.Reconstruction_screened_poisson["Merge all visible meshlayers"]= psim.Checkbox("Merge all visible meshlayers",self.Reconstruction_screened_poisson["Merge all visible meshlayers"])

            psim.PushItemWidth(50)
            _, self.Reconstruction_screened_poisson["Reconstruction Depth"]=psim.InputInt("Reconstruction Depth", self.Reconstruction_screened_poisson["Reconstruction Depth"])
            _, self.Reconstruction_screened_poisson["Adaptive Octree"]=psim.InputInt("Adaptive Octree Depth",self.Reconstruction_screened_poisson["Adaptive Octree"])
            _, self.Reconstruction_screened_poisson["Conjugate Gradients"]=psim.InputInt("Conjugate Gradients",self.Reconstruction_screened_poisson["Conjugate Gradients"])
            _, self.Reconstruction_screened_poisson["Scale Factor"]=psim.InputFloat("Scale Factor",self.Reconstruction_screened_poisson["Scale Factor"])
            _, self.Reconstruction_screened_poisson["Minimum number of samples"]=psim.InputFloat("Minimum number of samples", self.Reconstruction_screened_poisson["Minimum number of samples"])
            _, self.Reconstruction_screened_poisson["Interpolation Weight"]=psim.InputFloat("Interpolation Weight", self.Reconstruction_screened_poisson["Interpolation Weight"])
            _, self.Reconstruction_screened_poisson["Gauss-Seidel_Relaxation"]=psim.InputInt("Gauss-Seidel-Relaxation", self.Reconstruction_screened_poisson["Gauss-Seidel-Relaxation"])
            psim.PopItemWidth()
            _, self.Reconstruction_screened_poisson["Confidence Flag"]=psim.Checkbox("Confidence Flag", self.Reconstruction_screened_poisson["Confidence Flag"])
            _, self.Reconstruction_screened_poisson["Pre-Clean"] = psim.Checkbox("Pre-Clean", self.Reconstruction_screened_poisson["Pre-Clean"])


        def APSS_marching_cubes(self):
            psim.PushItemWidth(50)
            _, self.Reconstruction_APSS_marching_cubes["MLS-Filter Scale"] = psim.InputFloat("MLS-Filterscale", self.Reconstruction_APSS_marching_cubes["MLS-Filter Scale"])
            _, self.Reconstruction_APSS_marching_cubes["Projection Accuracy (adv)"]=psim.InputFloat("Projection Accuracy (adv)",self.Reconstruction_APSS_marching_cubes["Projection Accuracy (adv)"])
            _, self.Reconstruction_APSS_marching_cubes["Projection- Max iterations(adv)"]=psim.InputInt("Projection- Max iterations(adv)", self.Reconstruction_APSS_marching_cubes["Projection- Max iterations(adv)"])
            _, self.Reconstruction_APSS_marching_cubes["MLS-spherical parameter"]=psim.InputFloat("MLS-spherical parameter", self.Reconstruction_APSS_marching_cubes["MLS-spherical parameter"])
            _, self.Reconstruction_APSS_marching_cubes["Accurate Normals"]=psim.Checkbox("Accurate Normals",self.Reconstruction_APSS_marching_cubes["Accurate Normals"])
            _, self.Reconstruction_APSS_marching_cubes["Grid Resolution"]=psim.InputInt("Grid Resolution", self.Reconstruction_APSS_marching_cubes["Grid Resolution"])
            psim.PopItemWidth()

        def Ball_pivoting(self):
            psim.PushItemWidth(50)
            _, self.Reconstruction_Ball_Pivoting["Pivoting Ball Radius"]=psim.InputFloat("Pivoting Ball Radius",self.Reconstruction_Ball_Pivoting["Pivoting Ball Radius"])
            _, self.Reconstruction_Ball_Pivoting["Clustering Radius"]=psim.InputFloat("Clustering Radius",self.Reconstruction_Ball_Pivoting["Clustering Radius"])
            _, self.Reconstruction_Ball_Pivoting["Angle threshold"]=psim.InputFloat("Angle threshold (degrees)",self.Reconstruction_Ball_Pivoting["Angle threshold"])
            _, self.Reconstruction_Ball_Pivoting["Delete original set of faces"]=psim.Checkbox("Delete original set of faces", self.Reconstruction_Ball_Pivoting["Delete original set of faces"])
            psim.PopItemWidth()

        def VCG(self):
            psim.PushItemWidth(50)
            _, self.Reconstruction_VCG["Voxel size"] =psim.InputFloat("Voxel size", self.Reconstruction_VCG["Voxel size"])
            _, self.Reconstruction_VCG["SubVol Splitting"]=psim.InputInt("SubVol Splitting", self.Reconstruction_VCG["SubVol Splitting"])
            _, self.Reconstruction_VCG["Geodesic Weighting"]=psim.InputFloat("Geodesic Weighting", self.Reconstruction_VCG["Geodesic Weighting"])
            _, self.Reconstruction_VCG["Show Result"]=psim.Checkbox("Show Result", self.Reconstruction_VCG["Show Result"])
            _, self.Reconstruction_VCG["Volume Laplacian Iter"]=psim.InputInt("Volume Laplacian Iter", self.Reconstruction_VCG["Volume Laplacian Iter"])
            _, self.Reconstruction_VCG["Widening"]=psim.InputInt("Widening", self.Reconstruction_VCG["Widening"])
            _, self.Reconstruction_VCG["Vertex Splatting"]=psim.Checkbox("Vertex Splatting",self.Reconstruction_VCG["Vertex Splatting"] )
            _, self.Reconstruction_VCG["Post Merge Simplification"]=psim.Checkbox("Post Merge Simplification", self.Reconstruction_VCG["Post Merge Simplification"])
            _, self.Reconstruction_VCG["Presmooth iter"]=psim.InputInt("Presmooth iter", self.Reconstruction_VCG["Presmooth iter"])
            psim.PopItemWidth()

    class Smoothing:
        def __init__(self, view_point_x, view_point_y, view_point_z):
            self.SmoothingOptions = ["Depth Smooth", "HC Laplacian Smooth", "Laplacian Smooth", "Laplacian Smooth (surface preserving)",
                                        "Scale Dependent Laplacian Smooth", "Taubin Smooth", "Two Step Smooth"]
            self.SmoothingOptions_Selected = self.SmoothingOptions[0]
            #Depth Smooth dicttionary
            self.DepthSmooth={"Smoothing steps"      : 3,
                              "view point"           : [view_point_x, view_point_y, view_point_z],
                              "Strength"             : 100,
                              "Affect only selection": False
                              }
            #HCLaplacian None
            #Laplacian smoothing
            self.Laplace    ={"Smoothing steps"      : 3,
                              "1D Boundary Smoothing":False,
                              "Cotangent weighting"  :False,
                              "Affect only selection":False
                             }

            #Laplacian smooth surface preserving
            self.Laplace_surf_preserv = {"Update section" : False,
                                         "Max Normal Dev" : 0.5,
                                         "Iterations"     : 1
                                        }
            #Scale dependent laplacian smoothing
            self.Scale_dep_Laplace  = {"Smoothing Steps"            :3,
                                       "delta"                      :1.0,
                                       "Affect only selected faces" : False
                                      }

            #Taubin smoothing
            self.Taubin = {"Lambda"                         : 0.5,
                           "Mu"                             : -0.53,
                           "Smoothing steps"                : 10,
                           "Affect only selected faces"     : False
                           }

            self.Two_Step = {"Smoothing Steps"              :  3,
                             "Feature Angle Threshold"      : 60,
                             "Normals Smoothing Steps"      : 20,
                             "Vertex Fitting Steps"         : 20,
                             "Affect only selected faces"   : False
                            }

        def Depth_smooth(self):
            psim.PushItemWidth(50)
            _, self.DepthSmooth["Smoothing steps"] = psim.InputInt("Smoothing Steps", self.DepthSmooth["Smoothing steps"])
            _, self.DepthSmooth["view point"][0] =psim.InputFloat("x", self.DepthSmooth["view point"][0])
            psim.SameLine()
            _, self.DepthSmooth["view point"][1] =psim.InputFloat("y", self.DepthSmooth["view point"][1])
            psim.SameLine()
            _, self.DepthSmooth["view point"][2] =psim.InputFloat("z", self.DepthSmooth["view point"][2])

            _, self.DepthSmooth["Strength"]      =psim.InputFloat("Strength", self.DepthSmooth["Strength"])
            _, self.DepthSmooth["Affect only selection"]= psim.Checkbox("Affect only selection", self.DepthSmooth["Affect only selection"])
            psim.PopItemWidth()


        def Laplacian_smooth(self):
            psim.PushItemWidth(50)
            _, self.Laplace["Smoothing steps"] = psim.InputInt("Smoothing steps", self.Laplace["Smoothing steps"])
            _, self.Laplace["1D Boundary Smoothing"] = psim.Checkbox("1D Boundary Smoothing", self.Laplace["1D Boundary Smoothing"])
            _, self.Laplace["Cotangent weighting"]  = psim.Checkbox("Cotangent weighting", self.Laplace["Cotangent weighting"])
            _, self.Laplace["Affect only selection"]= psim.Checkbox("Affect only selection", self.Laplace["Affect only selection"])
            psim.PopItemWidth()

        def Laplacian_smooth_surface_preserving(self):
            psim.PushItemWidth(50)
            _,self.Laplace_surf_preserv["Update section"] = psim.Checkbox("Update section", self.Laplace_surf_preserv["Update section"])
            _,self.Laplace_surf_preserv["Max Normal Dev"] = psim.InputFloat("Max Normal Dev", self.Laplace_surf_preserv["Max Normal Dev"])
            _,self.Laplace_surf_preserv["Iterations"]     = psim.InputInt("Iterations", self.Laplace_surf_preserv["Iterations"] )
            psim.PopItemWidth()

        def Scale_dependant_Laplacian_smooth(self):
            psim.PushItemWidth(50)
            _, self.Scale_dep_Laplace["Smoothing Steps"]            = psim.InputInt("Smoothing Steps", self.Scale_dep_Laplace["Smoothing Steps"])
            _, self.Scale_dep_Laplace["delta"]                      = psim.InputFloat("delta",self.Scale_dep_Laplace["delta"] )
            _, self.Scale_dep_Laplace["Affect only selected faces"] = psim.Checkbox("Affect only selected faces", self.Scale_dep_Laplace["Affect only selected faces"])
            psim.PopItemWidth()

        def Taubin_smooth(self):
            psim.PushItemWidth(50)
            _, self.Taubin["Lambda"]           = psim.InputFloat("Lambda", self.Taubin["Lambda"])
            _, self.Taubin["Mu"]               = psim.InputFloat("Mu", self.Taubin["Mu"])
            _, self.Taubin["Smoothing steps"]  = psim.InputInt("Smoothing steps",self.Taubin["Smoothing steps"])
            _, self.Taubin["Affect only selected faces"]   = psim.Checkbox("Affect only selected faces", self.Taubin["Affect only selected faces"] )
            psim.PopItemWidth()

        def Two_step_smooth(self):
            psim.PushItemWidth(50)
            _, self.Two_Step["Smoothing Steps"] =psim.InputInt("Smoothing Steps", self.Two_Step["Smoothing Steps"])
            _, self.Two_Step["Feature Angle Threshold"]=psim.InputFloat("Feature Angle Threshold", self.Two_Step["Feature Angle Threshold"])
            _, self.Two_Step["Normals Smoothing Steps"]=psim.InputInt("Normals Smoothing Steps", self.Two_Step["Normals Smoothing Steps"])
            _, self.Two_Step["Vertex Fitting Steps"] = psim.InputInt("Vertex Fitting Steps", self.Two_Step["Vertex Fitting Steps"])
            _, self.Two_Step["Affect only selected faces"]= psim.Checkbox("Affect only selected faces", self.Two_Step["Affect only selected faces"])
            psim.PopItemWidth()

    class GeometricMeasures:
        """Geomtric measures class """
        def __init__(self, ms, master):
            #Compute_measures
            self.master = master
            self.ms = ms
            self.MeasureOptions= ['Scale dependent quadric Fitting','Discrete Curvature','APSS Curvature', 'Geometric Measures', 'Geodesic Distance from given point', 'Topological measures']
            self.MeasureOptions_selected = self.MeasureOptions[0]

            self.CurvatureOptionsprincipalcurvature = {"Mean Curvature": True, "Gaussian Curvature": False, "Min Curvature": False, "Max Curvature": False, "Shape Index": False,
                                                        "CurvedNess": False}

            self.CurvatureScale = 10

            self.CurvatureOptions = {"Mean Curvature" : True, "Gaussian Curvature": False, "RMS Curvature": False, "ABS Curvature": False}



            self.CurvatureOptionsAPSS = {"Mean" : True, "Gauss": False, "K1": False, "K2": False, "ApproxMean": False}

            self.Reconstruction_APSS_curvature={"MLS-Filter Scale"                 :      2,
                                                     "Projection Accuracy (adv)"        : 0.0001,
                                                     "Projection- Max iterations(adv)"  :     15,
                                                     "MLS-spherical parameter"          :      1,
                                                     "Accurate Normals"                 :   True,
                                                     "Grid Resolution"                  :    200,
                                                    }

            #Geometric measures None
            self.Geod_dista_from_point={"view point": [1,2,3],
                                        "Option": "View point",
                                        "Max Distance": 50.
                                        }

            #Topological measures

        def curvature_by_scale_dependend_quadric_fitting(self):
            psim.PushItemWidth(50)
            _, self.CurvatureScale = psim.InputFloat("Scale %", self.CurvatureScale)
            psim.PopItemWidth()
            for Option in self.CurvatureOptionsprincipalcurvature.keys():
                _, self.CurvatureOptionsprincipalcurvature [Option]=psim.Checkbox(Option, self.CurvatureOptionsprincipalcurvature [Option])
                if self.CurvatureOptionsprincipalcurvature [Option]:
                    for other in self.CurvatureOptionsprincipalcurvature .keys():
                        if other == Option:
                            continue
                        self.CurvatureOptionsprincipalcurvature [other]=False

            if(psim.Button('calculate')):
                for type in self.CurvatureOptions:
                    if self.CurvatureOptions[type]:
                        vertices = self.ms.current_mesh().vertex_matrix()
                        faces = self.ms.current_mesh().face_matrix()
                        ms2 = pymeshlab.MeshSet()
                        m = pymeshlab.Mesh(vertex_matrix = vertices, face_matrix= faces)
                        ms2.add_mesh(m)
                        ms2.compute_curvature_principal_directions_per_vertex(scale = pymeshlab.PercentageValue(self.CurvatureScale), curvcolormethod = type, method='Scale Dependent Quadric Fitting')
                        self.ms.add_mesh(ms2.current_mesh())
                        self.master.layers.append(Polymeshlabfusion.Mesh(self.ms,f"colorized by curvature {self.master.get_mesh_num()}", color=(0.2, 0.2, 0.2)))


        def Discrete_Curvature(self):
            for Option in self.CurvatureOptions.keys():
                _, self.CurvatureOptions[Option]=psim.Checkbox(Option, self.CurvatureOptions[Option])
                if self.CurvatureOptions[Option]:
                    for other in self.CurvatureOptions.keys():
                        if other == Option:
                            continue
                        self.CurvatureOptions[other]=False

            if(psim.Button('calculate')):
                for type in self.CurvatureOptions:
                    if self.CurvatureOptions[type]:
                        self.ms.compute_scalar_by_discrete_curvature_per_vertex(curvaturetype = type)





        def APSS_curvature(self):
            psim.PushItemWidth(50)
            _, self.Reconstruction_APSS_curvature["MLS-Filter Scale"] = psim.InputFloat("MLS-Filterscale", self.Reconstruction_APSS_curvature["MLS-Filter Scale"])
            _, self.Reconstruction_APSS_curvature["Projection Accuracy (adv)"]=psim.InputFloat("Projection Accuracy (adv)",self.Reconstruction_APSS_curvature["Projection Accuracy (adv)"])
            _, self.Reconstruction_APSS_curvature["Projection- Max iterations(adv)"]=psim.InputInt("Projection- Max iterations(adv)", self.Reconstruction_APSS_curvature["Projection- Max iterations(adv)"])
            _, self.Reconstruction_APSS_curvature["MLS-spherical parameter"]=psim.InputFloat("MLS-spherical parameter", self.Reconstruction_APSS_curvature["MLS-spherical parameter"])
            for Option in self.CurvatureOptionsAPSS.keys():
                _, self.CurvatureOptionsAPSS[Option]=psim.Checkbox(Option, self.CurvatureOptionsAPSS[Option])
                if self.CurvatureOptionsAPSS[Option]:
                    for other in self.CurvatureOptionsAPSS.keys():
                        if other == Option:
                            continue
                        self.CurvatureOptionsAPSS[other]=False

            psim.PopItemWidth()

            if(psim.Button('Calculate')):
                for type in self.CurvatureOptionsAPSS:
                    if self.CurvatureOptionsAPSS[type]:
                        self.ms.compute_curvature_and_color_apss_per_vertex(filterscale = self.Reconstruction_APSS_curvature["MLS-Filter Scale"],
                                                                            projectionaccuracy= self.Reconstruction_APSS_curvature["Projection Accuracy (adv)"],
                                                                            maxprojectioniters= self.Reconstruction_APSS_curvature["Projection- Max iterations(adv)"],
                                                                            sphericalparameter=self.Reconstruction_APSS_curvature["MLS-spherical parameter"],
                                                                            selectiononly = False,
                                                                            curvaturetype = type)

        def Geometric_Measures(self):
            if(psim.Button("Compute Geometric measures")):
                geometric_measures = self.ms.get_geometric_measures()
                for key in geometric_measures: print(f"{key}: {geometric_measures[key]}")



        def Geod_distance_from_point(self):
            psim.PushItemWidth(50)
            _, self.Geod_dista_from_point["view point"][0] =psim.InputFloat("x", self.Geod_dista_from_point["view point"][0])
            psim.SameLine()
            _, self.Geod_dista_from_point["view point"][1] =psim.InputFloat("y", self.Geod_dista_from_point["view point"][1])
            psim.SameLine()
            _, self.Geod_dista_from_point["view point"][2] =psim.InputFloat("z", self.Geod_dista_from_point["view point"][2])
            psim.SameLine()
            _, self.Geod_dista_from_point["Max Distance"] =psim.InputFloat("Max Distance", self.Geod_dista_from_point["Max Distance"])

            if(psim.Button('Compute')):
                self.ms.compute_scalar_by_geodesic_distance_from_given_point_per_vertex(startpoint = np.array([self.Geod_dista_from_point["view point"][0],
                                                                                                               self.Geod_dista_from_point["view point"][1],
                                                                                                               self.Geod_dista_from_point["view point"][2]]),

                                                                                        maxdistance = pymeshlab.PercentageValue(self.Geod_dista_from_point["Max Distance"]))


            psim.PopItemWidth()

        def Topological_measures(self):
            if(psim.Button("Compute Topologoical measures")):
                print(self.ms.get_topological_measures())


    class Photoslices:
        def __init__(self, meshSet, resolutions, ranges):

            #resolutions
            self.resolution_x = resolutions[2]
            self.resolution_y = resolutions[1]
            self.resolution_z = resolutions[0]

            #lower limits of volume
            self.start_x = ranges[0][0]
            self.start_y = ranges[1][0]
            self.start_z = ranges[2][0]

            #upper limits of volume
            self.end_x = ranges[0][1]
            self.end_y = ranges[1][1]
            self.end_z = ranges[2][1]

            #MeshSet
            self.ms = meshSet
            self.Slices = None
            self.meshes= []

        def Photoslicing(self):
            psim.PushItemWidth(50)
            _, self.start_x = psim.InputFloat("start x", self.start_x)
            psim.SameLine()
            _, self.end_x   = psim.InputFloat("end x", self.end_x)
            psim.SameLine()
            _, self.resolution_x = psim.InputInt("Resolution x", self.resolution_x)
            psim.PopItemWidth()

            psim.PushItemWidth(50)
            _, self.start_y = psim.InputFloat("start y", self.start_y)
            psim.SameLine()
            _, self.end_y   = psim.InputFloat("end y", self.end_y)
            psim.SameLine()
            _, self.resolution_y = psim.InputInt("Resolution y", self.resolution_y)
            psim.PopItemWidth()

            psim.PushItemWidth(50)
            _, self.start_z = psim.InputFloat("start z", self.start_z)
            psim.SameLine()
            _, self.end_z   = psim.InputFloat("end z", self.end_z)
            psim.SameLine()
            _, self.resolution_z = psim.InputInt("Resolution z", self.resolution_z)
            psim.PopItemWidth()



def main():
    ms = pymeshlab.MeshSet()
    #ms.load_new_mesh('Experiment-78+curvature.ply')
    # points=ms.current_mesh().vertex_matrix()
    # faces=ms.current_mesh().face_matrix()
    poly = PolyscopeGUI()


if __name__ == '__main__':
    main()
