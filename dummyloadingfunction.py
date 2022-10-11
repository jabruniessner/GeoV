import numpy as np
import glob
import os

def dummyloadingfunction(folder):
    current_directory=os.getcwd()
    os.chdir(folder)
    for file in glob.glob("viewpointno*.npz"):
        print(file)
        array=np.load(file)
        print(array['position'])
