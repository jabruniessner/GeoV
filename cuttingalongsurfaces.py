import pymeshlab
import numpy as np
import math
from PIL import Image
import tifffile
import tkinter.filedialog as tk
import sys
import cv2


TEMP = sys.stdout
#take a photo of the cross section
def take_cross_section_photo(vertex_matrix, rangex, rangey, resolutionx, resolutiony):

    blackimage = np.zeros(shape=(resolutionx, resolutiony), dtype=np.int8)
    stepsizex = (rangex[1]-rangex[0])/resolutionx
    stepsizey = (rangey[1]-rangey[0])/resolutiony
    for i in vertex_matrix:
        x = math.floor((i[0]-rangex[0])/stepsizex)-1
        y = math.floor((i[1]-rangey[0])/stepsizey)-1
        if x > resolutionx-1 or y >resolutiony-1:
            continue
        blackimage[x, y]= 255


    return blackimage

def binarize(image, threshold):
    x = (image>threshold)*255
    return x.astype(np.uint8)

def meanblur(image):
    return cv2.blur(image.astype(np.uint8), (3, 3)).astype(np.uint8)



def save_images(image, name):
    img = Imagge.fromarray(image)
    img.save(name)



def create_cuts(values, mesh):

    #the values for ranges and resolutions
    resolution = values['resolutions']
    rangex = values['ranges']['x']
    rangey = values['ranges']['y']
    rangez = values['ranges']['z']


    ms = pymeshlab.MeshSet()
    ms.add_mesh(mesh)


    #we need the stepsize in z direction
    stepsizez = (rangez[1]-rangez[0])/resolution['z']
    stepsizex = (rangex[1]-rangex[0])/resolution['x']
    stepsizey = (rangey[1]-rangey[0])/resolution['y']


    vertex_matrices=np.array([[0,0,0]])
    meshes = []
    for i in range(resolution['z']):
        ms.set_current_mesh(0)
        ms.generate_polyline_from_planar_section(planeaxis='Z Axis', planeoffset = i*stepsizez + rangez[0])
        ms.set_current_mesh(i+1)
        v=ms.current_mesh().vertex_matrix()
        vertex_matrices=np.concatenate((vertex_matrices,v) , axis=0)
        meshes.append(v)

    return vertex_matrices, meshes





def save_image_as():

    for i in vertex_matrices:
        image = take_cross_section_photo(i, rangex, rangey, resolution['x'], resolution['y'])
        image = meanblur(image)
        image = binarize(image, 27)
        image = meanblur(image)
        image = binarize(image, 27)
        image = meanblur(image)
        image = binarize(image, 27)

        images.append(image)


    images=np.array(images)
    tifffile.imwrite( file2, images)

    sys.stdout = open(file2[:-4]+'.txt', 'w')
    print(f'The voxelsize in x direction: {stepsizex}' )
    print(f'The voxelsize in y direction: {stepsizey}' )
    print(f'The voxelsize in z direction: {stepsizez}' )
    sys.stdout.close()
    sys.stdout = TEMP

    print('I am done here!')
