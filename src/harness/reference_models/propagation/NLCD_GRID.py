from reference_models.geo import nlcd
import numpy as np


def computeGridNlcd(pdLat,pdLon):
    terrainNlcd = nlcd.NlcdDriver()
    nRow = len(pdLat)
    nCol = len(pdLon)
    p2nNlcdValue = [[0] * int(nCol) for i in range(int(nRow))]
    p2sRegion = [[0] * int(nCol) for i in range(int(nRow))]
    for i in range(0,nRow):
        #i = nRow - 1
        dLat1 = pdLat[i]
        for j in range(0,nCol):
            #j=nCol-1
            #print i, j
            dLon1 = pdLon[j]
            nNlcdValue= terrainNlcd.GetLandCoverCodes(dLat1,dLon1)
            region = nlcd.GetRegionType(nNlcdValue)
            p2nNlcdValue[i][j]=nNlcdValue
            p2sRegion[i][j] = region
    return p2nNlcdValue, p2sRegion

def computePointNlcd(dLat,dLon):
    terrainNlcd = nlcd.NlcdDriver()
    nNlcdValue = terrainNlcd.GetLandCoverCodes(dLat, dLon)
    return nNlcdValue