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
#KML Parser
#WG4_KML.py
#
#James (Jody) Neel
#james.neel@federatedwireless.com
#Federated Wireless
#v0.1   July 20, 2015 (Initial Contribution)
#v0.11  July 28 - Census Tract Handling; forced placemark name to string
#
#Contributed to WINNF 3550 WG4
#################
#DESCRIPTION
#
#Provides methods for moving data between KML files and shapely objects
#
#Classes:
#   Area - a collection of polygons (e.g., some ground based radar exclusion zones)
#   Coordinate - a 2-D point (x,y) extended to include a name and icon color
#   KMLShapes - parses KML files to Shapely polygons, writes coordinates to KML file
#       loadKMLShapeFile - read in KML file to KMLShapes.areas
#       writeKMLCoordinatesFile - writes coordinates to KML file
#

#   =============
#   Copyright 2015 James Neel, Federated Wireless All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#   =============

#################
#Libraries
#################
#libraries for kml parsing
from lxml import etree
from pykml import parser
from pykml.parser import Schema
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
import re #regular expressions - Perl - for simpler string handling in parsing
#import zipfile #use if we end up supporting kmz files
#sample...
#with zipfile.ZipFile(arg1) as kml_file:
#        with kml_file.open('doc.kml', 'r') as kml_file2:
#            doc = parser.parse(kml_file2).getroot()


#libraries for shapely shapes
import shapely
from shapely.geometry import Polygon
from shapely.geometry import Point


class Area: #simplify management of KML files with multiple exterior polygons in a single placemark (multi-geometries)
    def __init__(self):
        self.name = ''
        self.pgons = []

class Coordinate: #simplify coloring/ naming of Coordinates
    def __init__(self):
        self.name ='default name'
        self.colorInt = 0
        self.x = 0
        self.y = 0

        self.colorMap = []
        self.colorMap.append('http://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png')
        self.colorMap.append('http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png')
        self.colorMap.append('http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png')

class KMLShapes: #main useful class - implements read / write / parse functions
    def __init__(self):
        self.areas = []
        self.ReadKMLShapeFileName = ''
        self.WriteKMLShapeFileName = 'test.kml'
        self.KMLName = 'test KML'

    def writeKMLCoordinatesFile(self,coordinates):
        self.writeKMLShapeFile(WriteKMLShapeFileName)
        return

    def loadKMLShapeFile(self):
        self.loadKMLShapeFile(ReadKMLShapeFileName)
        return

    def loadCensusKMLShapeFile(self,fileName):
        #different format from exclusionZones
        #optional multiGeometry
        #no inner ring?

        with open(fileName, 'r') as tmp_file:
            doc = parser.parse(tmp_file).getroot()

            for pmrk in doc.Document.Folder.Placemark:#should probably handle the case where there is no Folder
                tmpArea = Area()
                tmpArea.name = str(pmrk.name)

                print tmpArea.name

                #one multigeomtery per placemark
                #possibly multiple polygons

                try: #may not be a multigeometry
                                        
                    for pg in pmrk.MultiGeometry.Polygon:
                        #must be an ounter boundary
                        #tmp_coordinate_list = pg.outerBoundaryIs.LinearRing.coordinates.text.split(',')

                        #remove leading tab and newline characters
                        try:
                            tmp_str = pg.outerBoundaryIs.LinearRing.coordinates.text.strip()

                            #split by commas and spaces 
                            tmp_coordinate_list = re.split(' |,',tmp_str)
                            
                            ext_pt_long = [float(x) for x in tmp_coordinate_list[0::3]]
                            ext_pt_lat = [float(x) for x in tmp_coordinate_list[1::3]]
                            #don't need elevation which would be [2::3]
                            ext_pts = zip(ext_pt_long,ext_pt_lat) #different behavior in Python 3.0

                            #print ext_pts
                        except:
                            print 'ERROR: no outer boundary exists for ' + tmpArea.name
                            raise #unworkable exception - all areas need an outer boundary

                        tmp_PGON = Polygon(ext_pts)
                        tmpArea.pgons.append(tmp_PGON)
                        print 'Multiple polygon'
                        
                except: #single polygon
                    print 'single polygon'
                    pg = pmrk.Polygon
                    #remove leading tab and newline characters
                    try:
                        tmp_str = pg.outerBoundaryIs.LinearRing.coordinates.text.strip()

                        #split by commas and spaces 
                        tmp_coordinate_list = re.split(' |,',tmp_str)
                        
                        ext_pt_long = [float(x) for x in tmp_coordinate_list[0::3]]
                        ext_pt_lat = [float(x) for x in tmp_coordinate_list[1::3]]
                        #don't need elevation which would be [2::3]
                        ext_pts = zip(ext_pt_long,ext_pt_lat) #different behavior in Python 3.0

                        #print ext_pts
                    except:
                        print 'ERROR: no outer boundary exists for ' + tmpArea.name
                        raise #unworkable exception - all areas need an outer boundary

                    tmp_PGON = Polygon(ext_pts)
                    tmpArea.pgons.append(tmp_PGON)
            
                self.areas.append(tmpArea)
        return

       

    def loadKMLShapeFile(self,fileName):
        with open(fileName, 'r') as tmp_file:
            doc = parser.parse(tmp_file).getroot()

            for pmrk in doc.Document.Folder.Placemark:#should probably handle the case where there is no Folder
                tmpArea = Area()
                tmpArea.name = str(pmrk.name) #sometimes name is a number and python wasn't handling correctly

                print tmpArea.name

                #one multigeomtery per placemark
                #possibly multiple polygons
                for pg in pmrk.MultiGeometry.Polygon:
                    #must be an ounter boundary
                    #tmp_coordinate_list = pg.outerBoundaryIs.LinearRing.coordinates.text.split(',')

                    #remove leading tab and newline characters
                    try:
                        tmp_str = pg.outerBoundaryIs.LinearRing.coordinates.text.strip()

                        #split by commas and spaces 
                        tmp_coordinate_list = re.split(' |,',tmp_str)
                        
                        ext_pt_long = [float(x) for x in tmp_coordinate_list[0::3]]
                        ext_pt_lat = [float(x) for x in tmp_coordinate_list[1::3]]
                        #don't need elevation which would be [2::3]
                        ext_pts = zip(ext_pt_long,ext_pt_lat) #different behavior in Python 3.0

                        #print ext_pts
                    except:
                        print 'ERROR: no outer boundary exists for ' + tmpArea.name
                        raise #unworkable exception - all areas need an outer boundary
                    
                    #may be an inner boundary to polygon (not part of the area)
                    #White Sands has an inner ring

                    int_pts = []

                    int_exists = False
                    
                    try: 
                        for inBound in pg.innerBoundaryIs:
                            tmp_str = pg.innerBoundaryIs.LinearRing.coordinates.text.strip()
                            tmp_coordinate_list = re.split(' |,',tmp_str)
                            
                            int_pt_long = [float(x) for x in tmp_coordinate_list[0::3]]
                            int_pt_lat = [float(x) for x in tmp_coordinate_list[1::3]]
                            #don't need elevation which would be [2::3]
                            int_pts = zip(int_pt_long,int_pt_lat) #different behavior in Python 3.0
                            
                            #tmp_coordinate_list = pg.innerBoundaryIs.LinearRing.coordinates.text.split(',0 ')

                            #int_pt_long = [float(x) for x in tmp_coordinate_list[0::3]]
                            #int_pt_lat = [float(x) for x in tmp_coordinate_list[1::3]]
                            #int_pts = zip(int_pt_long,int_pt_lat) #different behavior in Python 3.0
                            print 'inner boundary exists'
                            int_exists = True
                        
                    except:
                        print 'no inner boundary exists'
                        #okay exception, many areas lack inner linear rings

                    if int_exists:
                        tmp_PGON = Polygon(ext_pts,[int_pts])
                    else:     
                        tmp_PGON = Polygon(ext_pts,int_pts)
            
                    tmpArea.pgons.append(tmp_PGON)

                self.areas.append(tmpArea)
        return

    def writeKMLCoordinatesFile(self,fileName, coordinates):
        
        doc = KML.kml()
        name_object = KML.name(self.KMLName)
        KML.append(name_object)
        
        fld = KML.Folder() #do we want this?

        k=0
        for pt in coordinates:
            nm_str = pt.name#'Pt ' + str(k)
            sty = KML.Style(KML.IconStyle(KML.Icon(KML.href(pt.colorMap[pt.colorInt]))))
            k_pt = KML.Point(KML.coordinates(pt.x,',',pt.y,',0 '))
            pm = KML.Placemark(
                KML.name(nm_str),
                sty,
                k_pt)
            fld.append(pm)    
            k = k+1
            
        doc.append(fld)

        # output a KML file
        outfile = file(fileName,'w')
        outfile.write(etree.tostring(doc, pretty_print=True))

        assert Schema('kml22gx.xsd').validate(doc)

        #print etree.tostring(doc, pretty_print=True) #debugging echo to screen

        return


