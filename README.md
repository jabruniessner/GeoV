# GeoV
This project aims to be a toolbox for the geometric analysis of Biological vesicles from microscopy data


## Thanks
First of all, I would like to say that this project is largely based on the two python packages pymeshlab and polyscope, found under the following links:

https://polyscope.run/py/

and 

https://github.com/cnr-isti-vclab/PyMeshLab

polyscope was developed by Nick Sharp and others and pymeshlab was developed by The Visual computing lab- ISTI - CNR

Many thanks for the great work the developers have done and providing these tools as Open Source for everyone to use

## License

The parts that I have written are licensed under the GPL v. 3 license found here:

https://www.gnu.org/licenses/gpl-3.0.de.html

If this tool should contribute to a publication please cite as:

@misc{GeoV,    
  title = {GeoV},   
  author = {Jakob Niessner, Yannik Dreher and Kerstin Göpfrich},   
  note = {https://github.com/jabrucohee/GeoV/edit/main/README.md},   
  year = {2022}   
}

The website of our (my former) group:

https://goepfrichgroup.de/

## A small request at the beginning:

As this project is only now about to become public many bugs and incompletness cannot be avoided. We are therefore very thankful for any bug report feedback inspiration and new ideas of what could still be implemented. We always try to help! Especially if there is a problem with the installation don't hesitate to ask for help!

## Installation

The program is currently unfortunaltely only supported on Linux (Tested on Ubuntu) and Windows. For Mac a more complicated manual installation process is provided. Since it only depends on a bunch of python scripts, the installation is simply equivalent to installing all the necessary python packages. (except for polyscope, I made one or two slight changes to the source code, it therefore needs to be compiled.)

### Linux:
The included bash script "Installation.sh" creates a virtual environment installs all necessary packages and then compiles the right version of Polyscope.
If you are interested in this, simply run in your terminal `git clone --recursive https://github.com/jabrucohee/GeoV.git` cd to the cloned directory and run `bash Installation.sh`

### Windows:
If you would like to use Windows, there is also an installation script that can be used. Again, just run `git clone --recursive https://github.com/jabrucohee/GeoV.git` and then run `Installation.bat`. This will create a virtual environement install all the necessary dependencies and compile polyscope.

### Mac:
As already mentioned above, you can try installing all dependencies required and then then start it manually.








