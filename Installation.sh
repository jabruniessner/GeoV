#!/bin/bash
pip3 install virtualenv
virtualenv reconProgram
source reconProgram/bin/activate
pip3 install -r requirements.txt
cd polyscope-py
python3 setup.py install
cd ..

