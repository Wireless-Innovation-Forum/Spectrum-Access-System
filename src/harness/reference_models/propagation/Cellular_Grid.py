import numpy as np
from math import ceil
from reference_models.geo import vincenty

def ComputeCellularGrid(nlandsea_scenario):
    if (nlandsea_scenario == 1):
        dNorthLatitude = +38.909794
        dWestLongitude = -77.043228
        dEastLongitude = -74.737878895394061
        dSouthLatitude = +37.107938100254628
        dGridGranularity = 500.00
        pdGridPointLat, pdGridPointLon, nVerticalPointQuantity, nHorizontalPointQuantity = ComputeCellularGridPoints(dNorthLatitude, dSouthLatitude, dEastLongitude, dWestLongitude, dGridGranularity)
        dApLat = pdGridPointLat[0]
        dApLon = pdGridPointLon[0]
        return nVerticalPointQuantity, nHorizontalPointQuantity,pdGridPointLat, pdGridPointLon,dApLat,dApLon
    elif (nlandsea_scenario == 2):
        dApLat = 39.960987
        dApLon =-75.158146
        dRadialSpacingKm = 99.00*0.001
        dRadialAngle = 2.0
        dMaxDistance = 80.0
        p2dGridPointLat, p2dGridPointLon, nVerticalPointQuantity, nHorizontalPointQuantity = computeRadials(dApLat, dApLon, dRadialSpacingKm, dRadialAngle, dMaxDistance)
        return p2dGridPointLat, p2dGridPointLon, nVerticalPointQuantity, nHorizontalPointQuantity, dApLat, dApLon

    elif (nlandsea_scenario == 6):
        dApLon = -71.118836
        dApLat = 42.369509
        nTileLat = 43
        nTileLon = -72
        nSubtileLatIdx = 17
        nSubtileLonIdx = 26
        nSubtileSizeQty, pdSubTileLat, pdSubTileLon = compute2ArcSecGrid(nTileLat, nTileLon, nSubtileLatIdx, nSubtileLonIdx)
        return nSubtileSizeQty, nSubtileSizeQty, pdSubTileLat, pdSubTileLon, dApLat, dApLon

def computeRadials(dApLat, dApLon, dRadialSpacingKm, dRadialAngle, dMaxDistance):
    nRadialQty = int(360.00/dRadialAngle)
    nDistanceLen = int(dMaxDistance / dRadialSpacingKm)
    pdDistance = np.zeros(nDistanceLen)
    pdRadialAngle = np.zeros(nRadialQty)
    for j in range(0, nDistanceLen):
        pdDistance[j]= j*dRadialSpacingKm
    for i in range(0,nRadialQty):
        pdRadialAngle[i] = i * dRadialAngle
    p2dGridPointLat = np.zeros((nRadialQty, nDistanceLen))
    p2dGridPointLon = np.zeros((nRadialQty, nDistanceLen))
    for i in range(0, nRadialQty):
        for j in range(0,nDistanceLen):
            if (pdDistance[j]==0):
                p2dGridPointLat[i][j], p2dGridPointLon[i][j] = dApLat, dApLon
            else:
                p2dGridPointLat[i][j] , p2dGridPointLon[i][j], _ = vincenty.GeodesicPoint(dApLat, dApLon, pdDistance[j], pdRadialAngle[i])
    return p2dGridPointLat, p2dGridPointLon, nRadialQty, nDistanceLen


def compute2ArcSecGrid(nTileLat,nTileLon,nSubtileLatIdx,nSubtileLonIdx):
    nSubtileSizeQty = 60
    n2ArcSecTileQty = 3600 / 2
    nSubtileQty = n2ArcSecTileQty / nSubtileSizeQty
    pdSubTileLat = nTileLat - (np.arange(0,nSubtileSizeQty)/float(n2ArcSecTileQty)) - (nSubtileSizeQty*nSubtileLatIdx/float(n2ArcSecTileQty))
    pdSubTileLon = nTileLon + (np.arange(0,nSubtileSizeQty)/float(n2ArcSecTileQty)) + (nSubtileSizeQty*nSubtileLonIdx/float(n2ArcSecTileQty))

    return nSubtileSizeQty, pdSubTileLat, pdSubTileLon

def ComputeCellularGridPoints(dNorthLatitude, dSouthLatitude, dEastLongitude, dWestLongitude, dGridGranularity):
    dHorizontalMoveAngle = 90.00
    dVerticalMoveAngle = 180.00
    dVerticalDistanceKm, dAzimuth, dBackAzimuth = vincenty.GeodesicDistanceBearing(dNorthLatitude, dWestLongitude, dSouthLatitude, dWestLongitude, accuracy=1.0E-12)
    dVerticalEdge = dVerticalDistanceKm * 1000.00

    dHorizontalDistanceKm, dAzimuth, dBackAzimuth=vincenty.GeodesicDistanceBearing(dNorthLatitude, dWestLongitude, dNorthLatitude, dEastLongitude, accuracy=1.0E-12)
    dHorizontalEdge = dHorizontalDistanceKm * 1000.00

    nHorizontalPointQuantity = ceil(dHorizontalEdge / float(dGridGranularity))
    nVerticalPointQuantity = ceil(dVerticalEdge / float(dGridGranularity))

    nNumCols = nHorizontalPointQuantity
    nNumRows = nVerticalPointQuantity
    dHorizontalInterDistance = dHorizontalEdge / float(nHorizontalPointQuantity - 1)
    dVerticalInterDistance = dVerticalEdge / float(nVerticalPointQuantity - 1)
    dStartLatitude = dNorthLatitude
    dStartLongitude = dWestLongitude
    pdGridPointLat = np.zeros(int(nVerticalPointQuantity))
    pdGridPointLon = np.zeros(int(nHorizontalPointQuantity))
    pdGridPointLat[0] = dStartLatitude
    pdGridPointLon[0] = dStartLongitude
    for i in range(1, int(nNumCols)):
        _, pdGridPointLon[i], _ = vincenty.GeodesicPoint(dStartLatitude, dStartLongitude, (dHorizontalInterDistance*0.001), dHorizontalMoveAngle)
        dStartLongitude = pdGridPointLon[i]
    for j in range(1, int(nNumRows)):
        pdGridPointLat[j], _, _ = vincenty.GeodesicPoint(pdGridPointLat[j-1], pdGridPointLon[0], (dVerticalInterDistance * 0.001), dVerticalMoveAngle)
    return pdGridPointLat,pdGridPointLon, nVerticalPointQuantity, nHorizontalPointQuantity