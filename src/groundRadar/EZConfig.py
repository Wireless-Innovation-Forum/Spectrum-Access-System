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

#Parser for reading in Excluson Zone Test Configuration Information from XML file
#10/26 - not yet complete (not commented, LocPoint..)


from xml.dom.minidom import parse
import xml.dom.minidom

class LocPoint:#not currently used... probably use to convert coordinate as string to shapely point
    def __init__(self):
        self.long = 0
        self.lat = 0

class TestType:
    def __init__(self):
        self.type = 'NA'
        self.numPoints = 0
        self.Pgon = 'Outer' #Inner, Outer, Pgon # (for areas with multiple polygons)

class ManualTest(TestType):
    def __init__(self):
        TestType.__init__(self)
        
        self.pts = []
        
class GaussianTest(TestType):#can't call it 2DGaussian (leading numeric)
    def __init__(self):
        TestType.__init__(self)
        self.std_dev = 0
        self.center = 'Centroid'

class EdgeTest(TestType):
    def __init__(self):
        TestType.__init__(self)
        self.std_dev = 0
        

class EZTest:
    def __init__(self):
        self.name = 'default name'
        self.tests = []

class EZConfig:
    def __init__(self):
        self.testAreas = []

    def parseFile(self,filename):

        DOMTree = xml.dom.minidom.parse(filename)
        collection = DOMTree.documentElement

        # Get all the tests in the collection
        EZTestList = collection.getElementsByTagName('EZTest')

        for EZTestItem in EZTestList:
            tmp_EZTest = EZTest()

            EZTestName = EZTestItem.getElementsByTagName('Name')[0]
            tmp_EZTest.name = EZTestName.childNodes[0].data
            #print "Name: %s" % tmp_EZTest.name       

            testList = EZTestItem.getElementsByTagName('Test')
            tmpTestList = []
            
            for t in testList:
                tmp = t.getElementsByTagName('Type')[0]
                tmpType = tmp.childNodes[0].data
                #print "Type: %s" % tmpType 

                if tmpType =='Edge':
                    tmpTest = EdgeTest()
                    tmpTest.type = 'Edge'
                    tmpTest.Pgon = 'Outer'
                    
                
                    tmp = t.getElementsByTagName('numPoints')[0]
                    tmpNum = tmp.childNodes[0].data

                    tmp = t.getElementsByTagName('Stddev')[0]
                    tmpstd = tmp.childNodes[0].data

                    tmpTest.numPoints = tmpNum
                    tmpTest.std_dev = tmpstd

                    try:
                        tmp = t.getElementsByTagName('Pgon')[0]
                    
                        tmpInnerOuter = tmp.childNodes[0].data

                        #print 'Im an innie' + tmpInnerOuter
                        
                    except:
                        tmpInnerOuter = 'Outer'

                    tmpTest.Pgon = tmpInnerOuter

                elif tmpType =='Gaussian':
                    tmpTest =GaussianTest()
                    tmpTest.type = 'Gaussian'

                    tmp = t.getElementsByTagName('numPoints')[0]
                    tmpNum = tmp.childNodes[0].data

                    tmp = t.getElementsByTagName('Stddev')[0]
                    tmpstd = tmp.childNodes[0].data

                    tmp = t.getElementsByTagName('Center')[0]
                    tmpCenter = tmp.childNodes[0].data

                    tmpTest.numPoints = tmpNum
                    tmpTest.std_dev = tmpstd
                    tmpTest.center = tmpCenter

                    try:
                        tmp = t.getElementsByTagName('Pgon')[0]
                    
                        tmpInnerOuter = tmp.childNodes[0].data

                        #print 'Im an innie' + tmpInnerOuter
                        
                    except:
                        tmpInnerOuter = 'Outer'

                    tmpTest.Pgon = tmpInnerOuter
                tmpTestList.append(tmpTest)
                
            tmp_EZTest.tests = tmpTestList
            self.testAreas.append(tmp_EZTest)   

        
