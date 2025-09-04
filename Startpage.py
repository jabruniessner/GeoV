from tkinter import *
import numpy as np
from PIL import ImageTk, Image
from tkinter import filedialog, ttk
import os
import glob
import Backendstartpage
import thresholdfinder
import czifile
import tifffile
import polyscope as ps
import platform


class StartpageGUI:
    '''This is the main GUI class. '''
    def __init__(self, master, program):
        system = platform.uname().system

        #Defining the main appearance of the window
        self.master=master
        self.duty=program
        self.master.title('GeoV')
        if system=='Linux':
            self.master.geometry("1535x601")
        else:
            self.master.geometry("1180x512")


        #The entry box for the folder path
        self.FolderBox=Entry(self.master, text="Enter Folder Path", width=42, fg="grey")
        self.FolderBox.insert(0, "Enter folder path")
        #the key bindings
        self.FolderBox.bind('<Return>', self.hit_enter)
        self.FolderBox.bind('<1>', self.being_clicked)


        #Varaible to specifiy what happens when Entry box is first clicked (clearing place holder etc.)
        self.__first=True

        #Variable to specify what happens when the threshold box is first being_clicked
        self.__firstthresh=True


        #Default value of the channelnum:
        self.__channelnum = 2

        #Default value for Folder
        self.folder = os.getcwd()

        #Resolution of currently selected image
        self.__resolution = (0,0,0)
        self.__ranges = ((0,0), (0,0), (0,0))


        # button for folder browse
        self.FolderBrowse=ttk.Button(self.master, text="Browse", command= self.UpdateFolder)
        #buttons for the calculation options
        self.filelist=Listbox(self.master, height=30, width=84)
        self.filelist.bind('<1>',self.being_clicked_filelist)

        #widgets for the choice of the threshold
        self.threshold=Entry(self.master, width=10, fg="grey")
        self.threshold.insert(0, "AUTOMATIC")
        self.threshold.bind('<1>', self.being_clicked_thresh)
        self.medianfilter=Entry(self.master, width=4)
        self.medianfilter.insert(0, "1")
        self.medianfilterlabel=ttk.Label(self.master, text="The current choice of filtersize: ")


        self.buttonthresh=ttk.Button(self.master, text="Thresholdfinder", command=self.threshold_finder)
        self.thresholdtitle=Label(self.master, text="The threshold is :")

        #widgets for the choice of the channel:
        self.channellabel=ttk.Label(self.master, text="Current choice of the channel (numbers start from 1):")
        self.channelentry=Entry(self.master, width=10)
        self.channelentry.insert(0, self.__channelnum)


        #This is for the positioning of the widgets


        #file and folder choice
        self.filelist.grid(row=1, column=0, rowspan=35, columnspan=4, ipadx=20, padx=0)
        self.FolderBox.grid(row=0, column=0, columnspan=2,padx=0)
        self.FolderBrowse.grid(row=0, column = 2, ipadx=34)

        #threshold choice
        self.thresholdtitle.grid(row=0, column=4, columnspan=2)
        self.threshold.grid(row=0, column = 6, sticky="w", ipadx=57)
        self.medianfilter.grid(row=0, column=8, sticky='w')
        self.medianfilterlabel.grid(row=0, column=6, columnspan=2, sticky='e')
        self.buttonthresh.grid(row=0, column=8, padx = 50,sticky='w')

        #channelchoice
        self.channellabel.grid(row=2, column=4, columnspan=3, sticky= "e")
        self.channelentry.grid(row=2, column=7)



        #create the voxelsizeentries:
        self.VoxelsizesMenu = self.Voxelsizes(self.master, 4, 5, self.start_3D_viewer_pc)


        #Initialize values for the first time
        self.values = self.get_values_from_GUI()



    def UpdateFolder(self):
        self.folder=filedialog.askdirectory()
        if self.folder != "":
            self.being_clicked(True)
            self.FolderBox.delete(0, END)
            self.FolderBox.insert(0, self.folder)
            self.filelist.delete(0, END)
            for name in glob.glob(self.folder+"/*.czi"):
                self.filelist.insert(0, name[len(self.folder)+1:])

            for name in glob.glob(self.folder+"/*.tif"):
                self.filelist.insert(0, name[len(self.folder)+1:])


    def being_clicked(self, x):
        if self.__first == True:
            print("Hello world")
            self.FolderBox.delete(0, END)
            self.FolderBox.configure(fg="black")
        self.__first = False

    def being_clicked_thresh(self, x):
        if self.__firstthresh == True:
            print("Hello world")
            self.threshold.delete(0, END)
            self.threshold.configure(fg="black")
        self.__firstthresh = False

    def being_clicked_filelist(self, x):
        '''This happens when the file is clicked on'''
        file = self.folder+r"/"+self.filelist.get(ANCHOR)

        if file[-4:]==".czi":
            czi=czifile.CziFile(file)

            num_dims = len(np.squeeze(czi.asarray()).shape)
            if num_dims == 3:
                self.__resolutions = np.squeeze(czi.asarray()).shape
            elif num_dims == 4:
                self.__resolutions = np.squeeze(czi.asarray())[0].shape

            #self.__resolutions = np.squeeze(czi.asarray())[0].shape
            metadata = czi.metadata()
            x, y, z = self.duty.findvoxelsizes(metadata)
            self.VoxelsizesMenu.voxel_size_x.delete(0, END)
            self.VoxelsizesMenu.voxel_size_y.delete(0, END)
            self.VoxelsizesMenu.voxel_size_z.delete(0, END)

            self.VoxelsizesMenu.voxel_size_x.insert(0,f"{x:.4f}")
            self.VoxelsizesMenu.voxel_size_y.insert(0,f"{y:.4f}")
            self.VoxelsizesMenu.voxel_size_z.insert(0,f"{z:.4f}")

            #breakpoint()


            self.__ranges = ((0, x*self.__resolutions[2]), (0, y*self.__resolutions[1]),(0, z*self.__resolutions[0]))
            print(self.__resolutions)

        elif file[-4:]==".tif":
            tiff = tifffile.TiffFile(file)
            self.__resolutions = np.squeeze(tiff.asarray()).shape

            try:
                x = float(self.VoxelsizesMenu.voxel_size_x.get())
                y = float(self.VoxelsizesMenu.voxel_size_y.get())
                z = float(self.VoxelsizesMenu.voxel_size_z.get())
                self.__ranges = ((0, x*self.__resolutions[2]), (0, y*self.__resolutions[1]),(0, z*self.__resolutions[0]))
                print(self.__resolutions)

            except ValueError:
                print('voxelsizes not found, please enter them manually')
                return

            self.__ranges = ((0, x*self.__resolutions[2]), (0, y*self.__resolutions[1]),(0, z*self.__resolutions[0]))
            print(self.__ranges)
            print(self.__resolutions)













    def hit_enter(self, x):
        self.duty.CurrentFolder = self.FolderBox.get()

    def threshold_finder(self):
        self.__channelnum = int(self.channelentry.get())-1
        file=self.folder+r"/"+self.filelist.get(ANCHOR)
        czi=thresholdfinder.get_czi_images(file, self.__channelnum)
        window=Toplevel(self.master)
        Thresholdchooser=thresholdfinder.Imageviewer(window, czi)
        button_done=ttk.Button(window, text="Use!", 
                               command= lambda : [self.threshold.delete(0, "end"),
                                                  self.threshold.insert(0, Thresholdchooser.threshold_external),
                                                  self.medianfilter.delete(0, "end"),
                                                  self.medianfilter.insert(0,Thresholdchooser.denoisfiltersize),
                                                  window.withdraw(),
                                                  window.destroy(), 
                                                  window.update()])
        button_done.grid(row=4, column=0)

    def get_values_from_GUI(self):
        '''This funtion manges the getting of the variables from the GUI'''
        try:
            thresh=int(self.threshold.get())

        except ValueError:
            thresh=None

        try:
            filtersize=int(self.medianfilter.get())
        except ValueError:
            filtersize=1

        try:
            voxelx = float(self.VoxelsizesMenu.voxel_size_x.get())
            voxely = float(self.VoxelsizesMenu.voxel_size_y.get())
            voxelz = float(self.VoxelsizesMenu.voxel_size_z.get())
        except ValueError:
            voxelx = 1
            voxely = 1
            voxelz = 1

        try:
            channelnum = int(self.channelentry.get())-1
        except ValueError:
            channelnum = 2

        return {"channel number": channelnum,"filtersize": filtersize,"threshold": thresh, "voxel size x": voxelx, "voxel size y": voxely, "voxel size z": voxelz,
         "view point selection mode": "Automatic"}

    def calculate_pc_from_folder(self):
        self.values = self.get_values_from_GUI()
        self.duty.CurrentFolder =self.FolderBox.get()
        variables=self.get_values_from_GUI()
        self.duty.point_cloud_from_folder(self.values)

    def calculate_pc_from_file(self):
        self.values = self.get_values_from_GUI()
        self.duty.CurrentFolder = self.FolderBox.get()
        variables=self.get_values_from_GUI()
        self.duty.pointcloud_from_file(self.filelist.get(ANCHOR), self.values)


    def start_3D_viewer_pc(self):
        '''This function is called, when the button is clicked'''
        import viewer3D
        self.duty.CurrentFolder = self.FolderBox.get()
        file=self.filelist.get(ANCHOR)
        values=self.get_values_from_GUI()
        self.duty.start_3D_viewer_pc(file, values, self.__resolutions, self.__ranges)

    class Voxelsizes:
        def __init__(self, master, xposition: int, yposition: int, start_3D_viewer_function):
            '''This governs the part where the voxelsizes are entered'''

            self.master = master
            self.title = ttk.Label(self.master, text = "Voxelsizes in microns:")

            self.x = ttk.Label(self.master, text="x :")
            self.y = ttk.Label(self.master, text="y :")
            self.z = ttk.Label(self.master, text="z :")

            self.voxel_size_x = Entry(self.master, width = 6)
            self.voxel_size_y = Entry(self.master, width = 6)
            self.voxel_size_z = Entry(self.master, width = 6)
            self.button_3Dviewer = ttk.Button(self.master, text="3D Viewer", command=start_3D_viewer_function)

            self.title.grid(row=yposition, column=xposition, columnspan=2, sticky="w")
            self.x.grid(row=yposition+1, column=xposition+1)
            self.y.grid(row=yposition+1, column=xposition+2)
            self.z.grid(row=yposition+1, column=xposition+3)

            #Finding the voxelsizes
            self.voxel_size_x.grid(row=yposition+2, column=xposition+1)
            self.voxel_size_y.grid(row=yposition+2, column=xposition+2)
            self.voxel_size_z.grid(row=yposition+2, column=xposition+3)

            self.button_3Dviewer.grid(row=yposition+2, column=xposition+4, ipadx=7, padx=10)








def main():
    program=Backendstartpage.ReconProgram()
    root=Tk()
    #root.iconbitmap('Icon2.ico')
    GUI=MainGUI(root, program)
    root.mainloop()


if __name__ == '__main__':
    main()
