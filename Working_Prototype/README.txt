SYSC 4907 Helicopter GUI

System formatted for windows, filepaths will need to be changed for MAC/linux

.log file format
indexes for lights and objects start at 1, time in seconds
all log files must start with a call to CREATE
CREATE:
time,filepath,x,y,z,r,g,b,pitch,yaw,roll,transparency,nametag
CREATE,0000.00,bell_412.obj,0,0,0,0,125,255,0,0,0,0.6,Flight_demo

MODIFY:
time,object-index,x,y,z,r,g,b,pitch,yaw,roll,transparency,nametag
MODIFY,0000.50,1,0,0.1,0,0,125,255,5,0,0,0.6,Flight_demo

SET_CAMERA:
time,type(1-free,2-orbit),elevation,azimuth,(x,y,z)-for free cam
SET_CAMERA,0001.00,2,15,45
SET_CAMERA,0001.50,1,0,45,20,-10,-20

ADD_LIGHT: only placeable in reference to first object
time,x,y,z,r,g,b
ADD_LIGHT,0000.22,0,0,0,255,0,0

MODIFY_LIGHT:
time,index,r,g,b
MODIFY_LIGHT,0008.75,1,255,0,0

NEW_FILE:
time,filepath
NEW_FILE,0002.50,4907-test.log

RESTART_FILE:
time
RESTART_FILE,0003.00