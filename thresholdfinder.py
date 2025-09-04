from tkinter import *
from PIL import ImageTk, Image
import czifile
import tifffile
import numpy as np
from tkinter import ttk
import cv2
import time


def get_czi_images(imagefile, channelnum):
    if(imagefile[-4:]==".czi"):
        czi_file=czifile.CziFile(imagefile)
        czi= np.squeeze(czi_file.asarray())#[channelnum]
        if len(czi.shape)==4:
            czi=czi[channelnum]
        return czi
    elif(imagefile[-4:]==".tif"):
        tiff_file = tifffile.TiffFile(imagefile)
        tiff = np.squeeze(tiff_file.asarray()).astype("uint32")
        return tiff

def resize_stack(stack):
        if stack.shape[1]>600:
            stack = np.array([cv2.resize(img, dsize=(512, 512*int(stack.shape[2]/stack.shape[1])),
             interpolation=cv2.INTER_CUBIC) for img in stack])
        
        if stack.shape[2]>600:
            stack = np.array([cv2.resize(img, dsize=(512*int(stack.shape[1]/stack.shape[2]), 512),
             interpolation=cv2.INTER_CUBIC) for img in stack])

        return stack


class Imageviewer:
    def __init__(self, master, stack):
        self.master=master
        self.master.title('Threshold chooser')
        self.stack=resize_stack(stack)
        self.threshold_external = self.threshold = 255 #setting the default threshold
        self.current = 0
        #This is the size of the filter for the denoising step
        self.denoisfiltersize = 1

        self.background=Canvas(self.master, width=512, height=512, bg="black")
        self.background.grid(row=0, column=0)

        self.slider1=Scale(self.master, from_=0, to= np.max(stack), orient = HORIZONTAL,
                                command = self.updatethreshold)
        self.slider2=Scale(self.master, from_=0, to= len(stack)-1, orient = HORIZONTAL,
                                command = self.updateimages)
        self.denois = ttk.Button(self.master, text ="Remove noise", command=self.denoisingwindow)



        self.slider1.set(255)
        self.slider1.grid(row=1, column=0, ipadx=200)
        self.slider2.set(0)
        self.slider2.grid(row=2, column=0, ipadx= 200)
        p = self.binarize(0)
        self.x = ImageTk.PhotoImage(Image.fromarray(p.astype(np.uint8)))
        self.label=Label(self.master, image=self.x)
        self.label.grid(row=0, column=0)
        self.denois.grid(row=3, column=0)


    

    def updateimages(self, number: int):
        p=self.binarize(int(number))
        self.x=ImageTk.PhotoImage(Image.fromarray(p.astype('uint8'), mode='L'))
        self.label=Label(self.master,image=self.x, bg="black")
        self.label.grid(row=0, column=0)
        self.current=int(number)

    def binarize(self, number: int):
        return (self.stack[number]>=self.threshold)*255


    def updatethreshold(self, number: int):
        self.threshold_external=self.threshold = int(number)
        self.updateimages(self.current)


    def denoisingwindow(self):
        window=Toplevel(self.master)
        x=Denoisingchoice(window)

        def press_ok():

            def apply_blur():
                start=time.time()
                stack=self.stack
                stack_img=[]
                for i in stack:
                    blurred = cv2.medianBlur(i.astype(np.uint8), self.denoisfiltersize)
                    stack_img.append(blurred)
                self.stack = np.array(stack_img)

            self.stack = (self.stack>=self.threshold)*255
            self.denoisfiltersize=int(x.ksize.get())
            apply_blur()
            self.threshold= 127
            self.updateimages(self.current)
            self.slider1["state"]= "disabled"



        ok=ttk.Button(window, text="Ok", command=lambda:[press_ok(), window.destroy()])
        ok.grid(row=2, column=0, padx=20)


    






class Denoisingchoice:
    def __init__(self, master):
        self.master=master
        self.master.title("Radius")

        self.question=ttk.Label(self.master, text="Choose a size for the Filter:")
        self.question.grid(row=0, column=0, columnspan=2)
        self.ksize=Entry(self.master, width=5)
        self.ksize.grid(row=1, column=0, columnspan=2, pady=10)
        self.quit=ttk.Button(self.master, text="quit",command=self.master.destroy)
        self.quit.grid(row=2, column=1, padx=20)
        self.ksizevalue = None


def main():
    root=Tk()
    x=Denoisingchoice(root)
    root.mainloop()

if __name__ == '__main__':
    main()
