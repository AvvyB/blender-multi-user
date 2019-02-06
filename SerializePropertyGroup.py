import sys
import os


thirdPartyDir = "C:\\Users\\slumber\\repos\\phd\src\\2019_rcf\\libs"



if thirdPartyDir not in sys.path:
    print('Adding local modules dir to the path')
    sys.path.insert(0, thirdPartyDir)


import umsgpack
import bpy
import esper
from rna_xml import rna2xml

try:
    umsgpack.packb((getattr(bpy.data,'objects')))
except:
    pass