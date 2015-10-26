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

#################
#Area Functions
#WG4_Area.py
#
#James (Jody) Neel
#james.neel@federatedwireless.com
#Federated Wireless
#v0.1 July 20, 2015 (Initial Contribution)
#
#Contributed to WINNF 3550 WG4
#################
#DESCRIPTION
#
#Provides methods for moving data between KML files and shapely objects
#
#Functions:
#   generateTestPoints - generates test points for a line, uniformly distributed along the line,
#                        Gaussian perpindicular to the line
#
#Classes:
#   WG4Polygon - holds a polygon, includes functions for in / out of the polygon, 
#                can generate points for the area with 2D Gaussian about centroid of polygon
#
#################
#
#INSERT OPEN SOURCE TERMS HERE 
#################

#################
#Libraries
#################
import shapely
from shapely.geometry import Polygon
from shapely.geometry import Point

import numpy #for random numbers
import math #for rotations

def generateTestPoints(pt1, pt2, num_pts = 1, std=1):
    #generates Points (Shapely) according to the following rules
    #uniform distribution along line connecting Pt1 to Pt2
    #Gaussian distribution perpindicular to line connecting Pt1 to Pt2
    #uses math for sin,cos,atan2 (point rotation)
    #uses numpy for rand (uniform) and randn (normal Gaussian, scaled by std)
    
    dy = pt2.y - pt1.y
    dx = pt2.x - pt1.x
    d = math.sqrt(dx*dx +dy*dy)
    theta = atan2(dy,dx)
    cosTheta = math.cos(theta)
    sinTheta = math.sin(theta)

    rand_x = d*numpy.random.rand(1,num_pts)
    rand_y = std*numpy.random.randn(1,num_pts)

    tmp_pt = Point(0,0) #declaring a blank Point object
    pts_out = [] #unitialized list

    for k in range(0,num_pts):
        x = rand_x[0,k] #num_py uses arrays which needs different access
        y = rand_y[0,k] #also arrays are indexed from 0
        
        tmp_Pt.x = x*cosTheta - y*sinTheta + pt1.x
        tmp_Pt.y = x*sinTheta + y*cosTheta + pt1.y

        pts_out.append(tmp_Pt)

    return pt_out


class WG4Polygon:
    #contains a polygon 
    def __init__(self):
        self.my_polygon = Polygon([(0, 0), (1, 1), (1, 0)])#default triangle    
        
    def __init__(self, EZ_polygon):
        self.my_polygon = EZ_polygon

    def setPolygon(self,EZ_polygon):
        self.my_polygon = EZ_polygon

    def isAllowable(self, pl):
        #if the point is not in the exclusion zone polygon, then it's allowable     
        #return not(self.my_polygon.contains(pl))
        return not(pl.within(self.my_polygon))

    def contains(self, pl):
        return pl.within(self.my_polygon)
        #return self.my_polygon.contains(p1)

    def areAllowable(self, pt_list):
        good_list = []
        bad_list = []

        for p in pt_list:    
            if self.isAllowable(p):
                good_list.append(p)
            else:
                bad_list.append(p)
            
        return good_list,bad_list;

    def testPtsByArea(self,num_pts,std):
        center_pt = self.my_polygon.centroid

        bounds_box = self.my_polygon.bounds
        min_x = bounds_box[0]
        min_y = bounds_box[1]

        max_x = bounds_box[2]
        max_y = bounds_box[3]
        pt1 = Point(bounds_box[0], bounds_box[1])
        pt2 = Point(bounds_box[2], bounds_box[3])
        
        d = max(pt1.distance(center_pt), pt2.distance(center_pt))/math.sqrt(2)

        offset_values = d*std*numpy.random.randn(2,num_pts)

        pts_out = []
       

        for k in range(0,num_pts):
 
            tmp_x = center_pt.x + offset_values[0,k]
            tmp_y = center_pt.y + offset_values[1,k]
            tmp_p = Point(tmp_x,tmp_y)
            pts_out.append(tmp_p)

        return pts_out
    
