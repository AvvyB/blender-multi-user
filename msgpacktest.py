import sys
import os


thirdPartyDir = "C:\\Users\\slumber\\repos\\phd\src\\2019_rcf\\libs"



if thirdPartyDir in sys.path:
    print('Third party module already added')
else:
    print('Adding local modules dir to the path')
    sys.path.insert(0, thirdPartyDir)


import umsgpack
import bpy
import esper


#c = umsgpack.packb("test")
#print(umsgpack.unpackb(c))

