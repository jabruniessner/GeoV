import polyscope as ps
import polyscope.imgui as psim
import os
import getpass
import platform

SYSTEM = platform.uname().system




class Filedialog:
    Memberlist = []

    def __init__(self, name, formats, savingfunction, mode):
        self.mode = mode
        self.name = name
        self.savingfunction = savingfunction
        self.FileOptions=formats
        self.FileOptions_selected = self.FileOptions[0]
        self.changed= False
        self._is_active = False
        self._is_done = False
        #self.locations = ["Recently used", "Favourites", "Home", "Desktop", "Images", "Documents", "Downloads", "Music", "Videos"]
        self.locations = self.listinghomedirectory()

        if SYSTEM=="Linux":
            self.externallocations = self.listingadditionaldrives()

        self.cwd = os.getcwd()
        self.typing1=self.cwd
        self.typing2="Hello"
        self.NewFolderActive = False
        self.newfoldername = "Hello World"

        self.fileexistwarningwindow_active = False
        self.fileitem = None
        Filedialog.Memberlist.append(self)

    def set_file_options(self, options):
        self.FileOptions = options
        self.FileOptions_selected = self.FileOptions[0]


    def set_active(self, a_bool: bool):
        for mem in Filedialog.Memberlist:
            mem._is_active = False

        self._is_active = a_bool

    def get_active(self):
        return self._is_active

    def set_done(self, a_bool :bool):
        self._is_done = a_bool

    def get_done(self):
        return self._is_done

    def newfolder(self):
        psim.SetNextWindowPos((600, 300))
        psim.BeginChild(2, (500, 500))
        psim.EndChild()
        psim.SetNextWindowSize((300, 80))
        psim.Begin("Enter Name", True)
        entered, self.newfoldername = psim.InputText("", self.newfoldername)
        psim.SameLine()
        if(psim.Button('Create') or psim.IsKeyPressed(257)):
            if not os.path.exists(self.newfoldername):
                os.makedirs(self.newfoldername)

            self.NewFolderActive = False



        psim.End()

    def Overridewarning(self):
        psim.SetNextWindowPos((750, 400))
        psim.SetNextWindowSize((325, 105))

        psim.Begin("Warning", True)
        psim.TextUnformatted("Attention: The File you selected already exists")
        psim.TextUnformatted("Would you like to replace it?")
        if(psim.SmallButton("Ok")):
            self.fileexistwarningwindow_active = False
            self.typing2 = self.fileitem

        psim.SameLine()
        if(psim.SmallButton("Cancel")):
            self.fileexistwarningwindow_active = False

        psim.End()

    def currentlist(self):
        currentlist = os.listdir(self.cwd)
        #print(currentlist)
        for item in currentlist:
            if os.path.isdir(item) and item[0] != ".":
                psim.TextUnformatted('[Dir] '+ item)
                if(psim.IsItemClicked(0)):
                    try:
                        os.chdir(item)
                    except PermissionError:
                        ps.warning("Access denied!")

                    self.cwd = os.getcwd()
                    self.typing1 = os.getcwd()

            elif os.path.isfile(item) and item[-3:]== self.FileOptions_selected[-3:]:
                psim.TextUnformatted('[File] '+ item)
                if(psim.IsItemClicked(0)):
                    self.fileitem = item
                    self.fileexistwarningwindow_active = True

    def listinghomedirectory(self):
        dir = os.getcwd()
        os.chdir(os.path.expanduser("~"))
        dirlist = os.listdir()
        dirs = []
        for item in dirlist:
            if os.path.isdir(item) and item[0] != ".":
                dirs.append(item)
        os.chdir(dir)
        return dirs

    def listingadditionaldrives(self):
        dir = os.getcwd()
        os.chdir(os.path.abspath(os.sep))
        user = getpass.getuser()
        os.chdir("media/"+user)
        externallocs = os.listdir()
        os.chdir(dir)
        return externallocs





    def filedialog(self):
        psim.SetNextWindowPos((550, 200))
        psim.BeginChild(2, (500, 500))
        psim.EndChild()
        psim.SetNextWindowSize((900, 535))
        psim.Begin(self.name, True)

        psim.PushItemWidth(714)
        psim.BeginGroup()
        if(psim.ArrowButton('Up', 0)):
            os.chdir('..')
            self.cwd = os.getcwd()
            self.typing1 = self.cwd

        psim.SameLine()
        if(self.typing1.startswith("/media/"+getpass.getuser())):
            self.typing1 = self.typing1[len("/media/"+getpass.getuser())+1:]
        _, self.typing1 = psim.InputText("L", self.typing1)
        psim.SameLine()
        if(psim.Button("New Folder")):
            self.NewFolderActive = True

        psim.EndGroup()
        psim.PopItemWidth()


        psim.BeginChildFrame(4, (200, 400), 3)

        for loc in self.locations:
            psim.TextUnformatted(loc)
            if(psim.IsItemClicked(0)):
                os.chdir(os.path.expanduser("~"))
                os.chdir(loc)
                self.cwd = os.getcwd()
                self.typing1 = self.cwd

        if SYSTEM == "Linux":
            for loc in self.externallocations:
                psim.TextUnformatted(loc)
                if(psim.IsItemClicked(0)):
                    os.chdir("/media/"+getpass.getuser()+"/"+loc)
                    self.cwd = os.getcwd()
                    self.typing1 = loc

        psim.EndChildFrame()

        psim.SameLine()
        psim.BeginChildFrame(3,(685, 400), 2)
        self.currentlist()
        psim.EndChildFrame()


        psim.PushItemWidth(815)
        changed = psim.BeginCombo("", self.FileOptions_selected, 0)
        if changed:
            for val in self.FileOptions:
                _, selected = psim.Selectable(val, self.FileOptions_selected==val)
                if selected:
                    self.FileOptions_selected = val
            psim.EndCombo()
        psim.SameLine()

        if(psim.Button("Save")):
            self._is_active = False
            if self.mode == "File" and self.typing2 !="":
                self.savingfunction(self.typing2+self.FileOptions_selected[-4:])
            elif self.mode == "Dir":
                if self.typing2 != "":
                    self.savingfunction(self.typing2)
                else:
                    self.savingfunction(self.cwd)

        psim.PopItemWidth()



        psim.PushItemWidth(799)
        _, self.typing2 = psim.InputText("N", self.typing2)
        psim.SameLine()

        if(psim.Button("Quit", size=(65, 25))):
            self._is_active = False

        psim.PopItemWidth()
        psim.End()
        if self.NewFolderActive:
            self.newfolder()
        if self.fileexistwarningwindow_active:
            self.Overridewarning()


#FILEY = Filedialog()

def callback():
    if(psim.Button("Save File")):
        global FILEY
        FILEY.is_active = True
    if FILEY.is_active:
        FILEY.filedialog()

if __name__ == '__main__':

    ps.init()
    ps.set_user_callback(callback)
    ps.show()
