[//]: # (Image References)
[img_SystemOverview]: ./doc/img/System_overview.jpg "Entire system - big picture"

# BSM_Server
BSM Server for the CAV project

# Introduction
This repo is a part of the CAV project carried out by [Center of Advanced Transportation Technology](http://www.catt.umd.edu/). The big picture behind this project is to improve safety at the intersections. Namely: the objects at the intersection (cars, pedestrians, etc.) are detected and tracked, and then the information about detected objects is passed to all traffic participants that can receive it. 

The entire system is build of three components:
- Object detection and tracking 
- BSM server
- Broadcasting Equipment

![img_SystemOverview]

This repository contains the BSM Server component.

# Installation
Just download this repository, it doesn't use any non-standard python packages.
Written and tested with Python 3.

# Getting started
- Run the BSM server with: `python bsmserver.py`
- Open and run `./demo/client_push.ipynb` notebook. This notebook simulates the Detection and Tracking component by generating BSM messages.
- Open ./demo/Client_pull.ipynb notebook. 
    - If you are writing code for a broadcasting device (e.g. Cohda), you are interested in `Pull` functionality. 
    - If you are working on an external app, you are interested in `Check` functionality.
    
 