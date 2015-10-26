# Copyright 2015 Federated Wireless. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

#Sample script for running tests from xml definition file
#10/26 - not yet complete (code missing, not commented)

import EZConfig

import WG4_Area
import WG4_KML
import sys

from shapely.geometry import Point

EZC = EZConfig.EZConfig()

EZC.parseFile('EZ_config.xml')

#for testArea in EZC.testAreas:
#    print testArea.name
##    for t in testArea.tests:
##        print t.type
##        print t.numPoints
##        print t.std_dev

KS = WG4_KML.KMLShapes()
KS.loadKMLShapeFile('ground_based_exclusion_zones.kml')


for a in KS.areas:
    for testArea in EZC.testAreas:
        if a.name == testArea.name:
            print a.name
            #print 'test found'

            k = 0
            for t in testArea.tests:
                print 'test ' + str(k+1)
                print t.type

                if t.type == 'Gaussian':
                    if t.Pgon == 'Outer':
                        pg = a.pgons[0]
                    elif t.Pgon == 'Inner':
                        g = 1
                    else: #should be a number  
                        g = 2
                    
                    if t.center == 'Centroid':
                        cnt_pt = pg.centroid
                    else:
                        g = 3
                        #cnt_pt = #convert from string

                    #auto_pt_list = EZ_test.testPtsByArea(num_pts,stddev)#num_pts, std 
                    #good_list, bad_list = EZ_test.areAllowable(auto_pt_list)

                    
                        
                    

                #elif t.type == 'Edge':

                #elif t.type == 'Manual':
            
            
            break
    else:
        print 'no associated test for exclusion zone : ' + a.name

