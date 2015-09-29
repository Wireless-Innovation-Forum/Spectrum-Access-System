This directory contains raw and processed data files from the FCC
defining certain aspects of the 3.5GHz band operation context. Copyright
on data files is by their creators.

* DOC-334099A1.xlsx

    This is the raw spreadsheet containing the FCC-produced list of
    rural census tracts according to the definition in Part 96.3 (Rural Area).
    Referenced in the Public Notice DA 15-570 of June 25, 2015.
    The public notice is available at
    http://transition.fcc.gov/Daily_Releases/Daily_Business/2015/db0625/DA-15-750A1.pdf
    The data file is available at
    https://apps.fcc.gov/edocs_public/attachmatch/DOC-334099A1.xlsx

* 3.5GHzRuralCensusTracts.csv

    This is a CSV version of the DOC-334099A1.xlsx contents. The file
    has been exported as a comma-separated-value file with one column. The
    column contains the FIPS census tract code of those census tracts
    designated as rural.

* grandftr.pdf

    This is the raw source PDF file from the FCC containing grandfathered
    FSS earth stations for the 3650-3700 band.
    This file is referenced in the Report and Order 15-47 (Docket 12-354)
    footnote 30. It is linked from http://transition.fcc.gov/ib/sd/3650/
    and is available at
    http://transition.fcc.gov/ib/sd/3650/grandftr.pdf

* grandftr.xlsx

    This is a translation of the grandftr.pdf file to a spreadsheet format.
    The data table in the PDF file has been maintained intact.

* 3650_3700_GrandfatheredFSS.csv

    This is a CSV export of the grandftr.xlsx file. The comma-separated-value
    file has 8 columns, containing the city and state, latitude and longitude,
    and identifying information for each grandfathered FSS station.

* DOC-333151A1.xlsx

    This is the raw spreadsheet containing the FCC list of grandfathered
    FSS earth stations operating below 3700MHz for the CBRS.
    This file is referenced from the page at
    https://www.fcc.gov/cbrs-protected-fss-sites
    which is referenced in the Report and Order 15-47 (Docket 12-354) in
    96.17(a)-(b).
    It can be retrieved from
    https://apps.fcc.gov/edocs_public/attachmatch/DOC-333151A1.xlsx

* CBRS_3550_3700_GrandfatheredFSS.csv

    This is a CSV version of the DOC-333151A1.xlsx contents. The file has
    been exported as a comma-separated-value file with 20 columns. The
    columns contain information about the city, state, Call sign, operator,
    and latitude/longitude, operating frequency, and other metadata of
    grandfathered FSS earth stations. Each individual station is described
    by a row in the file.

* 3650_3700_radar_sites.kml

    This is a KML file containing the geometries described in the Report
    and Order 15-47 (Docket 12-354) in Footnote 31 and 33, and 90.1331(b)(1)
    and 96.15(b)(2):
    St. Inigoes, MD-—38° 10' N, 76° 23' W
    Pensacola, FL-—30° 21' 28" N, 87° 16' 26" W
    Pascagoula, MS--30° 22' N, 88° 29'W
    The KML file contains contours describing an 80km radius around
    these points. The labels of the points are the city names near where
    the centers are located.

* uscabdry.zip

    This is the raw zip file containing the FCC definition of the US-Canada
    border. It is linked from this page:
    https://www.fcc.gov/encyclopedia/white-space-database-administration-q-page
    and can be retrieved here:
    https://transition.fcc.gov/oet/info/maps/uscabdry/uscabdry.zip

* uscabdry.kmz

    This is a KMZ file with a representation of the boundary lines contained
    in the uscabdry.zip file. There are 17 line segments composing this
    boundary, each taken from a separate .MAP file in the uscabdry.zip file.

* uscabdry.kml

    This is a KML file produced by the script in src/data/uscabdry.py. It contains
    the US-CA border as processed from the source file by that script, which does
    data reduction, normalization, and some noise removal.

* us_mex_boundary.zip

    This is the raw zip file containing the FCC definition of the US-Mexico
    border. It is linked from this page:
    https://www.fcc.gov/encyclopedia/white-space-database-administration-q-page
    and can be retrieved here:
    http://www.ibwc.gov/GIS_Maps/downloads/us_mex_boundary.zip

* us_mex_boundary.kmz

    This is a KMZ file with a representation of the boundary line
    contained in the us_mex_boundary.zip Shapefile.

* usborder.kml

    This is a KML file produced by the script in src/data/usborder.py. It contains
    polygons representing the assignment authority of the SAS as described by the
    borders in FCC and NTIA source files. The borders represent the territorial sea
    boundary of US jurisdiction as modified by international sea borders reflected
    in the NOAA files, but modified by FCC border definitions for US-CA and US-MEX.

