import polyscope as ps
import polyscope.imgui as psim
import os
import getpass
import platform


SYSTEM = platform.uname().system


class Askopenfolder:
    Memberlist = []

    def __init__(self, name, formats, loadingfunction, mode):
        self.mode = mode
        self.name = name
        self.loadingfunction = loadingfunction
        self.FileOptions=formats
        self.FileOptions_selected = self.FileOptions[0]
        self.changed= False
        self._is_active = False
        self._is_done = False
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
        Askopenfolder.Memberlist.append(self)


    def set_active(self, a_bool: bool):
        for mem in Askopenfolder.Memberlist:
            mem._is_active = False

        self._is_active = a_bool

    def get_active(self):
        return self._is_active

    def set_done(self, a_bool :bool):
        self._is_done = a_bool

    def get_done(self):
        return self._is_done


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





    def askopenfile(self):
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

        if SYSTEM=="Linux":
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
        if(psim.Button("Open")):
            try:
                self._is_active = False
                self.loadingfunction(self.typing2)
            except TypeError:
                ps.error("You did not select an item!")

        psim.PopItemWidth()



        psim.PushItemWidth(799)
        _, self.typing2 = psim.InputText("N", self.typing2)
        psim.SameLine()

        if(psim.Button("Quit", size=(65, 25))):
            self._is_active = False

        psim.PopItemWidth()
        psim.End()
