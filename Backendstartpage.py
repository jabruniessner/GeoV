import glob
import numpy as np
import time
import pymeshlab
import os
import czifile
import cv2
import xml.etree.ElementTree as ET
import sys
import tifffile
import polyscope as ps




class ReconProgram:
    '''This is the main class of the Reconstruction Program'''

    def __init__(self, master):
        self.CurrentFolder=os.getcwd()
        self.temp=sys.stdout
        self.i = 0
        self.duty = master

    def findthresholdvalue(self, imgstack , position : int):
        '''This is an implementation of the Iso_data algorithm to find the threshold for the binarize automatically'''
        image=imgstack[position,:,:]
        t= 15*np.median(image)
        eps=0.001

        while 1:
            mL= 0 if image[image>=t].size==0 else image[image>=t].mean()
            mH= 0 if image[image<t].size==0 else image[image<t].mean()
            t_new = (mL+mH)/2
            if abs(t-t_new)<eps:
                break
            t=t_new
        print(f"The threshholdvalue for binarize was {t+2.5}")
        return round(t+2.5)

    def findvoxelsizes(self, metadata):
        '''This functions takes the metadata of a '''

        root=ET.fromstring(metadata)
        a=root.find('.//Distance[@Id="X"]')
        xvoxelsize=float(a[0].text)*10**6
        b=root.find('.//Distance[@Id="Y"]')
        yvoxelsize=float(b[0].text)*10**6
        c=root.find('.//Distance[@Id="Z"]')
        zvoxelsize=float(c[0].text)*10**6

        return (xvoxelsize, yvoxelsize, zvoxelsize)

    def findexistingmeshids(self, meshSet):
        ''' This functions is mostly an internal Routine. All meshes in a meshSet have an ID number.
        Her we index all exisitng Meshes in order to later find the largest.'''

        existingmeshids=[]
        i=0;
        while len(existingmeshids) < meshSet.number_meshes():
            if meshSet.mesh_id_exists(id=i) :
                existingmeshids.append(i)
            i += 1
        return existingmeshids

    def findlargestmesh(self, meshSet):
        #Find the largest mesh
        meshes = self.findexistingmeshids(meshSet)
        max_num_of_vertices = 0
        largest_mesh = 0
        for i in meshes:
            meshSet.set_current_mesh(i)
            if meshSet.current_mesh().vertex_number() > max_num_of_vertices:
                max_num_of_vertices = meshSet.current_mesh().vertex_number()
                largest_mesh = i

        return largest_mesh

    def pointcloud_finder(self, img, voxelsizex, voxelsizey, voxelsizez, thresh=None, filtersize=1):
        ''' This is the step, where the pointcloud is generated. The picture is first binarized and the position
         of the non-zero points are then written into an array, where the positions are multipklied with the voxelsizes.'''

        #in case there is no threshold given, we find one automatically
        if thresh==None:
            bildzahl=self.findmaxposition(img)
            thresh=self.findthresholdvalue(img, bildzahl)

        #This is where the actual pointcloud finding starts:
        if filtersize==1:
            print(img.shape)
            z, y, x = np.where(img>thresh)
            print()
            z=z*voxelsizez
            y=y*voxelsizey
            x=x*voxelsizex
            itemindex=np.array([x, y, z])
            points=np.transpose(itemindex)

            print(f"number of points in pointcloud {points.size/3}")

        else:
            img_bin = (img>thresh)*255
            images=[]
            for i in img_bin:
                g=cv2.medianBlur(i.astype(np.uint8), filtersize)
                images.append(g)
            stack=np.array(images)

            points=self.pointcloud_finder(stack, voxelsizex, voxelsizey, voxelsizez, thresh=127, filtersize=1)



        return points

    def images_from_file(self, file, channelnum):
            

            img=None
            if file[-4:]=='.czi':
                img = np.squeeze(czifile.CziFile(file).asarray()) #[channelnum]
                if img.shape == 4:
                    img = img[channelnum]
                
                print(img.shape)
            
            elif file[-4:]=='.tif':
                img = np.squeeze(tifffile.TiffFile(file).asarray())
            
            elif file[-4:]=='.lif':
                from readlif.reader import LifFile
                new_file = LifFile(file)
                img_0 = new.get_image(0)
                z_list = [i for i in img_0.get_iter_z(t=0, c=0)]
                liste = [np.array(new.get_frame(z=i, t=0, c=0)) for i in range(len(z_list))]
                img = np.array(liste)

            else:
                raise ValueError
            return img

    def get_points_from_file(self, file, values):
        os.chdir(self.CurrentFolder)
        img=self.images_from_file(file, values["channel number"])
        return self.pointcloud_finder(img, 
                                      values["voxel size x"], 
                                      values["voxel size y"], 
                                      values["voxel size z"], 
                                      values["threshold"], 
                                      values["filtersize"])

    def findmaxposition(self, imagestack):
        #Find the image with the highest intensities
        imagesums = []

        for i in range(imagestack.shape[0]):
            imagesums.append(np.sum(imagestack[i,:,:]))

        imagesums=np.array(imagesums)
        maxposition = np.argmax(imagesums)
        return maxposition

    def view_point_finder(self,values, point_cloud):
        if values['view point selection mode'] == 'Automatic':
            axes=np.transpose(point_cloud)
            view_point_x = np.mean(axes[0])
            view_point_y = np.mean(axes[1])
            view_point_z = np.mean(axes[2])
            return view_point_x, view_point_y, view_point_z

        else:
            return values['view point x'], values['view point y'], values['view point z']


    def calculate_normals(self, point_cloud, values):
        self.i = 0
        z_rescale_bool = values["z rescale mode"]
        print("We used z-rescale: " + str(z_rescale_bool))
        if not z_rescale_bool:
            self.i += 1
            ms=pymeshlab.MeshSet()
            m=pymeshlab.Mesh(point_cloud)
            ms.add_mesh(m)
            #if the view point should be found automtically
            view_point_selection = values["view_point_selection_mode"]
            view_pointx, view_point_y, view_point_z = self.view_point_finder(point_cloud, values)
            print("For the calculation of the normals, we used the following values: ")
            print("number of neighbours considered: "+str(values["number of neighbours normals"]))
            print("number of smoothiterations: " + str(values["smoothiterations"]))
            print("view_point_bool: " + str(values["view point bool"]))
            print("Position of the considered view_point: "+str(values["view point x"])+", " +str(values["view point y"])+", "+str(values["view point z"]))

            sub_sampling_points = int(0.29*ms.current_mesh().vertex_number())
            ms.generate_simplified_point_cloud(samplenum=sub_sampling_points, radius=pymeshlab.Percentage(0.231))
            ms.compute_normal_for_point_clouds(k=values["number of neighbours normals"], smoothiter=values["smoothiterations"], flipflag= values["view point bool"],
                                                viewpos=np.array([values["view point x"], values["view point y"], values["view point z"]]))

            return ms.current_mesh().vertex_matrix(), ms.current_mesh().vertex_normal_matrix()

        elif z_rescale_bool:
            self.i += 1
            point_cloud_rescaled = np.transpose(np.array([point_cloud[:, 0]/voxelsizes[0], point_cloud[:, 1]/voxelsizes[1], point_cloud[:,2]/voxelsizes[2]]))

            view_point_rescaled = [view_point_x/voxelsizes[0],view_point_y/voxelsizes[1], view_point_z/voxelsizes[2]]

            #creating unscaled normals
            points_unscaled, normals_unscaled = self.calculate_normals(point_cloud = point_cloud_rescaled, voxelsizes=None, view_point_selection=view_point_selection,
                                                        view_point_x = view_point_rescaled[0], view_point_y=view_point_rescaled[1], view_point_z=view_point_rescaled[2],
                                                        smoothiter=smoothiter, neighbour_num_normals=neighbour_num_normals,
                                                         view_point_bool=view_point_bool, z_rescale_bool = False)

            #creating rescaled normals
            rescale_matrix=np.diagflat([1/voxelsizes[0], 1/voxelsizes[1], 1/voxelsizes[2]])
            print(np.transpose(normals_unscaled).shape)
            normals_unnormalized = np.transpose(np.matmul(rescale_matrix,np.transpose(normals_unscaled)))
            normsofnormals = np.linalg.norm(normals_unnormalized, axis=1)[:, np.newaxis]
            normals = normals_unnormalized/normsofnormals
            points = np.transpose(np.array([points_unscaled[:, 0]*voxelsizes[0], points_unscaled[:, 1]*voxelsizes[1], points_unscaled[:,2]*voxelsizes[2]]))

            return points, normals

    def calculate_point_cloud(self, image, filename, foldername, values):
        points = self.pointcloud_finder(image, values["voxel size x"], values["voxel size y"], values["voxel size z"], values["threshold"], values["filtersize"])
        m = pymeshlab.Mesh(points)
        ms = pymeshlab.MeshSet()
        ms.add_mesh(m)
        ms.set_current_mesh(0)
        if values["outlierflag"]:
            ms.compute_selection_point_cloud_outliers(propthreshold=values["probability"], knearest=values["number of neighbours"])
            ms.meshing_remove_selected_vertices()

        ms.save_current_mesh(self.CurrentFolder+r"/"+foldername+r"/"+filename[:-4]+"+pointcloud.ply", binary=False)
        print("The file was saved under:", self.CurrentFolder+r"/"+foldername+r"/"+filename[:-4]+"+pointcloud.ply")

    def point_cloud_from_folder(self, values):
        '''This function is called when the button pointcloud from folder is pressed'''

        starttime = time.time()
        os.chdir(self.CurrentFolder)

        #Creates storage folder if it does not yet exist
        if not os.path.exists('Pointclouds'):
            os.makedirs('Pointclouds')

        if glob.glob('*.tif') != []:
            xyval, zval, Answer = Parameterfortiff.dialogbox("We found tifffiles, would you like them to be Analyzed?")
            if Answer == True:
                for j in glob.glob('*.tif'):
                    jobname = j[:-4]
                    sys.stdout=open(os.getcwd()+r"/Pointclouds/" + f"log"+jobname+"Pointcloud.txt", "w")
                    print(f"For the Anaysis of "+jobname+ ", we used/found the following values:")
                    tiff=tifffile.imread(j)
                    self.calculate_point_cloud(tiff,filename=j, foldername='Pointclouds', values=values)
                    print("the execution time was:","{0:.2f}".format(time.time()-starttime), "seconds")
                    sys.stdout.close()
                    sys.stdout = sys.temp


        for j in glob.glob('*.czi'):
            jobname = j[:-4]
            sys.stdout=open(os.getcwd()+r"/Pointclouds/" + f"log"+jobname+"Pointcloud.txt", "w")
            print(f"For the Anaysis of "+jobname+ ", we used/found the following values:")
            czi=czifile.CziFile(j)
            img =np.squeeze(czi.asarray())[values["channel number"],:,:,:]
            x, y, z =self.findvoxelsizes(czi.metadata())
            self.calculate_point_cloud(img,filename=j, foldername='Pointclouds', values = values)
            print("the execution time was:","{0:.2f}".format(time.time()-starttime), "seconds")
            sys.stdout.close()
            sys.stdout = self.temp

    def pointcloud_from_file(self, filename,  values):
        starttime = time.time()
        os.chdir(self.CurrentFolder)
        filetype = filename[-3:]

        foldername = filename[:-4]

        if not os.path.exists(foldername):
            os.makedirs(foldername)



        print("For the Anaysis, we used/found the following values:")
        if filetype == 'czi':
            czi= czifile.CziFile(filename)
            img = np.squeeze(czi.asarray())[values["channel number"],:,:,:]
            x, y, z = self.findvoxelsizes(czi.metadata())

        elif filetype == 'tif':
            img = tifffile.TiffFile(filename).asarray()[:, values["channel number"], :, :]
            xyval, zval, Answer = Parameterfortiff.dialogbox("This is a tifffile, if you want it to be analyzed you need to provide a voxelsize")
            x, y = xyval
            z = zval

        self.calculate_point_cloud(img,filename, foldername, values)
        print("the execution time was:", "{0:.2f}".format(time.time()-starttime), "seconds")

    def start_3D_viewer_pc(self, file, values, resolutions, ranges):
        import viewer3D
        points = self.get_points_from_file(file, values)
        x, y, z = self.view_point_finder(values, points)
        #self.duty.withdraw()
        viewer3D.PolyscopeGUI(self, file, values["channel number"], file[:-4], points, x, y, z, resolutions, ranges)
        #self.duty.deiconify()



    #def start_3D_viewer_surface():
