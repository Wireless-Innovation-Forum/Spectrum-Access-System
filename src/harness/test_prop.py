from reference_models.propagation import wf_hybrid
from reference_models.propagation import Cellular_Grid
from reference_models.geo import nlcd
from reference_models.geo import vincenty
import numpy as np


nStatistics = 1
if nStatistics==1:
    dReliability = -1
else:
    dReliability = 0.5

nScenarioIdx = 10
dCbsdAgl = 10.00
dUeAgl = 50.00
if (nScenarioIdx == 0):
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=0.5,cbsd_indoor='True',region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=dReliability,cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=0.5,cbsd_indoor='True',region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=dReliability,cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=0.5,cbsd_indoor='True',region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.316543, -81.345152, 50,reliability=dReliability,cbsd_indoor='True',region='RURAL')
    print "1 km - 80 km"
elif (nScenarioIdx == 1):
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=0.5,cbsd_indoor='True',region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=dReliability, cbsd_indoor='True', region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.749948, -81.590209, 50,reliability=dReliability, cbsd_indoor='True',region='RURAL')
    print "100 m - 1 km"
elif (nScenarioIdx == 2):
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.746849, -81.590209, 50,reliability=dReliability, cbsd_indoor='True',region='RURAL')
    print "100 m"
elif (nScenarioIdx == 3):
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(30.745948, -81.590209, 10, 30.00, -81.345152, 50,reliability=dReliability, cbsd_indoor='True',region='RURAL')
    print "Above 80 km"
elif (nScenarioIdx == 4): #Sam email subject "IAP Reference Model Output" on 03222018
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(42.125, -108.205, 75, 42.122, -108.2, 1.5,reliability=dReliability, cbsd_indoor='True',region='RURAL')
elif (nScenarioIdx == 5): #Sam email subject "IAP Reference Model Output" on 03222018
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(42.323, -108.0, 75, 42.25, -108.0, 1.5,reliability=dReliability, cbsd_indoor='True',region='RURAL')
elif (nScenarioIdx == 6): #Rohan's email on registration worker on 03282018 at 0720' do not use this in for loop below if (nScenarioIdx < 20):
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5, reliability=0.5,cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5, reliability=0.5,cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5, reliability=0.5,cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(42.369509, -71.118836, 25, 42.28500000, -71.02000000, 1.5,reliability=dReliability, cbsd_indoor='True',region='RURAL')
elif (nScenarioIdx == 7): #FSS 8.2
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(39.2291, -100.1, 7.6, 39.0119, -98.4842, 9.3,reliability=dReliability, cbsd_indoor='True',region='RURAL')
elif (nScenarioIdx == 8): #Hybrid 8.2
    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=0.5, cbsd_indoor='True', region='URBAN')
    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=dReliability, cbsd_indoor='True',region='URBAN')
    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=0.5, cbsd_indoor='True', region='SUBURBAN')
    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=0.5, cbsd_indoor='True', region='RURAL')
    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(39.0119, -98.4842, 9.3, 39.29888888888889, -98.6499999999999, 1.5,reliability=dReliability, cbsd_indoor='True',region='RURAL')
elif (nScenarioIdx == 9):
    nScenarioRun = 1
    nVerticalQty,nHorizontal, pdSubTileLat, pdSubTileLon, dApLat, dApLon = Cellular_Grid.ComputeCellularGrid(1)
    p2dLossSuburbanStat0 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dLossSuburbanStat1 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dLossUrbanStat0 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dLossUrbanStat1 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dLossRuralStat0 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dLossRuralStat1 = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dCbsdUeAngle = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
    p2dUeCbsdAngle = [[0] * int(nHorizontal) for i in range(int(nVerticalQty))]
elif (nScenarioIdx == 10):
    nScenarioRun = 2
    p2dGridPointLat, p2dGridPointLon, nRow, nCol, dApLat, dApLon = Cellular_Grid.ComputeCellularGrid(nScenarioRun)
    nMaxLat = np.amax(p2dGridPointLat)
    nMinLat = np.amin(p2dGridPointLat)
    nMaxLon = np.amax(p2dGridPointLon)
    nMinLon = np.amin(p2dGridPointLon)
    p2dLossUrbanStat0 = [[0] * nCol for i in range(nRow)]
    p2dLossUrbanStat1 = [[0] * nCol for i in range(nRow)]
    p2dLossSuburbanStat0 = [[0] * nCol for i in range(nRow)]
    p2dLossSuburbanStat1 = [[0] * nCol for i in range(nRow)]
    p2dLossRuralStat0 = [[0] * nCol for i in range(nRow)]
    p2dLossRuralStat1 = [[0] * nCol for i in range(nRow)]
    p2dCbsdUeAngle = [[0] * nCol for i in range(nRow)]
    p2dUeCbsdAngle = [[0] * nCol for i in range(nRow)]
elif (nScenarioIdx == 11):
    nScenarioRun = 6
    nSubtileSizeQty,_,pdSubTileLat, pdSubTileLon, dApLat, dApLon = Cellular_Grid.ComputeCellularGrid(6)
    p2dLossUrbanStat0 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]
    p2dLossUrbanStat1 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]
    p2dLossSuburbanStat0 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]
    p2dLossSuburbanStat1 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]
    p2dLossRuralStat0 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]
    p2dLossRuralStat1 = [[0] * nSubtileSizeQty for i in range(nSubtileSizeQty)]

if (nScenarioIdx == 10):
    np.savetxt('GridPoints_Lat_P.txt', p2dGridPointLat, delimiter=',',fmt='%.15f')
    np.savetxt('GridPoints_Lon_P.txt', p2dGridPointLon, delimiter=',',fmt='%.15f')
elif ((nScenarioIdx == 9) | (nScenarioIdx == 11)):
    np.savetxt('GridPoints_Lat_P.txt', pdSubTileLat, fmt='%.15f')
    np.savetxt('GridPoints_Lon_P.txt', pdSubTileLon, fmt='%.15f')
    nRow = len(p2dLossUrbanStat0)
    nCol = len(p2dLossUrbanStat0[0])

if (nScenarioIdx < 9):
    p2dLossUrbanStat0 = db_lossU0[0]
    p2dLossUrbanStat1 = db_lossU1[0]
    p2dLossSuburbanStat0 = db_lossS0[0]
    p2dLossSuburbanStat1 = db_lossS1[0]
    p2dLossRuralStat0 = db_lossR0[0]
    p2dLossRuralStat1 = db_lossR1[0]
    p2dCbsdUeAngle = db_lossU0[1][1]
    p2dUeCbsdAngle = db_lossU0[1][3]
    print(p2dLossUrbanStat0)
    print(p2dLossUrbanStat1)
    print(p2dLossSuburbanStat0)
    print(p2dLossSuburbanStat1)
    print(p2dLossRuralStat0)
    print(p2dLossRuralStat1)
    print(p2dCbsdUeAngle)
    print(p2dUeCbsdAngle)
else:
    if ((nScenarioIdx == 9) | (nScenarioIdx == 11)):
        for i in range(0,nRow):
            dUeLat = pdSubTileLat[i]
            for j in range(0,nCol):
                dUeLon = pdSubTileLon[j]
                print i,j
                dist, _, _ = vincenty.GeodesicDistanceBearing(dApLat, dApLon, dUeLat, dUeLon)

                if (((i == 0) & (j == 0)) | (dist == 0.0)):
                    p2dLossUrbanStat0[i][j] = 0
                    p2dLossUrbanStat1[i][j] = 0
                    p2dLossSuburbanStat0[i][j] = 0
                    p2dLossSuburbanStat1[i][j] = 0
                    p2dLossRuralStat0[i][j] = 0
                    p2dLossRuralStat1[i][j] = 0
                    p2dCbsdUeAngle[i][j] = 0
                    p2dUeCbsdAngle[i][j] = 0
                else:
                    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=0.5, cbsd_indoor='True',region='URBAN')
                    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl, reliability=dReliability, cbsd_indoor='True',region='URBAN')
                    db_lossS0 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=0.5, cbsd_indoor='True',region='SUBURBAN')
                    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl,reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
                    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl,reliability=0.5, cbsd_indoor='True', region='RURAL')
                    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl,reliability=dReliability, cbsd_indoor='True', region='RURAL')
                    p2dLossUrbanStat0[i][j] = db_lossU0[0]
                    p2dLossUrbanStat1[i][j]  = db_lossU1[0]
                    p2dLossSuburbanStat0[i][j] = db_lossS0[0]
                    p2dLossSuburbanStat1[i][j] = db_lossS1[0]
                    p2dLossRuralStat0[i][j] = db_lossR0[0]
                    p2dLossRuralStat1[i][j] = db_lossR1[0]
                    p2dCbsdUeAngle[i][j] = db_lossU0[1][1]
                    p2dUeCbsdAngle[i][j] = db_lossU0[1][3]
    elif (nScenarioIdx == 10):
        for i in range(0, nRow):
            for j in range(0, nCol):
                print i, j
                dUeLat = p2dGridPointLat[i][j]
                dUeLon = p2dGridPointLon[i][j]
                dist, _, _ = vincenty.GeodesicDistanceBearing(dApLat, dApLon, dUeLat, dUeLon)
                if (dist==0):
                    p2dLossUrbanStat0[i][j] = 0
                    p2dLossUrbanStat1[i][j] = 0
                    p2dLossSuburbanStat0[i][j] = 0
                    p2dLossSuburbanStat1[i][j] = 0
                    p2dLossRuralStat0[i][j] = 0
                    p2dLossRuralStat1[i][j] = 0
                    p2dCbsdUeAngle[i][j] = 0
                    p2dUeCbsdAngle[i][j] = 0
                else:
                    db_lossU0 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=0.5, cbsd_indoor='True',region='URBAN')
                    db_lossU1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl, reliability=dReliability, cbsd_indoor='True',region='URBAN')
                    db_lossS0= wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon, dUeAgl,reliability=0.5, cbsd_indoor='True',region='SUBURBAN')
                    db_lossS1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=dReliability, cbsd_indoor='True',region='SUBURBAN')
                    db_lossR0 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=0.5, cbsd_indoor='True',region='RURAL')
                    db_lossR1 = wf_hybrid.CalcHybridPropagationLoss(dApLat, dApLon, dCbsdAgl, dUeLat, dUeLon,dUeAgl, reliability=dReliability,cbsd_indoor='True', region='RURAL')
                    p2dLossUrbanStat0[i][j] = db_lossU0[0]
                    p2dLossUrbanStat1[i][j]  = db_lossU1[0]
                    p2dLossSuburbanStat0[i][j] = db_lossS0[0]
                    p2dLossSuburbanStat1[i][j] = db_lossS1[0]
                    p2dLossRuralStat0[i][j] = db_lossR0[0]
                    p2dLossRuralStat1[i][j] = db_lossR1[0]
                    p2dCbsdUeAngle[i][j] = db_lossU0[1][1]
                    p2dUeCbsdAngle[i][j] = db_lossU0[1][3]
    np.savetxt('GridPoints_Rem_Ur0P.txt', p2dLossUrbanStat0, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_Rem_Ur1P.txt', p2dLossUrbanStat1, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_Rem_Sb0P.txt', p2dLossSuburbanStat0, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_Rem_Sb1P.txt', p2dLossSuburbanStat1, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_Rem_Rr0P.txt', p2dLossRuralStat0, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_Rem_Rr1P.txt', p2dLossRuralStat1, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_CbsdUeP.txt', p2dCbsdUeAngle, delimiter=',', fmt='%.6f')
    np.savetxt('GridPoints_UeCbsdP.txt', p2dUeCbsdAngle, delimiter=',', fmt='%.6f')