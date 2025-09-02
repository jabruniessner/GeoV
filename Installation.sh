#!/bin/bash
pip3 install virtualenv
virtualenv reconProgram
source reconProgram/bin/activate
pip install -r requirements.txt
cd polyscope-py
python -m pip install .
cd ..

