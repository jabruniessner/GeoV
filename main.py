import numpy as np
import viewer3D
import Startpage
from tkinter import *
import Backendstartpage
import polyscope as ps



def main():
    ps.set_program_name("Program")
    ps.init()
    root=Tk()
    program=Backendstartpage.ReconProgram(root)
    startpage = Startpage.StartpageGUI(root, program)
    root.mainloop()




if __name__ == '__main__':
    main()
