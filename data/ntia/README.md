This directory contains data files from the NTIA defining protection
geometries for federal incumbent protection in the 3.5GHz band.
Copyright on data files is by their creators.

* DPA_KML_vX.Y.pdf 

   Format definition for DPA KML files (both E-DPA.kml and P-DPA.kml).
   
* E-DPAs.kml

   The ESC-based DPA definition. This is a KML file defining each DPA and associated parameters.

* P-DPAs.kml
 
   The portal-based DPA definition. This is a KML file defining each DPA and associated parameters.

* GB_PART90_EZ.kml

   This is a KML file defining the Ground based and Part90 Exclusion zones.
   

The following files are provided for simulation and study purpose only, and not used in test harness:

* Urban_Areas_3601.kmz
    
    This is a KMZ file defining the US urban areas as provided by the Census bureau. 
    Used only for simulation and benchmark purposes.
    

The following files are provided for historical reasons and are currently not used:

* ground_based_exclusion_zones.kml

    This is a KML file defining inland exclusion zones for incumbent
    federal radar operations. It is referenced from
    http://www.ntia.doc.gov/category/3550-3650-mhz in the April 14, 2015
    filing with the FCC available here:
    http://www.ntia.doc.gov/fcc-filing/2015/ntia-letter-fcc-commercial-operations-3550-3650-mhz-band
    It can be retrieved from
    http://www.ntia.doc.gov/files/ntia/publications/ground_based_exclusion_zones.kml
    

* shipborne_radar_envelope_exclusion_zones.kml

    This is a KML file defining coastal exclusion zone boundaries for
    incumbent federal radar operations. It is referenced from
    http://www.ntia.doc.gov/category/3550-3650-mhz in the April 14, 2015
    filing with the FCC available here:
    http://www.ntia.doc.gov/fcc-filing/2015/ntia-letter-fcc-commercial-operations-3550-3650-mhz-band
    It can be retrieved from
    http://www.ntia.doc.gov/files/ntia/publications/shipborne_radar_envelope_exclusion_zones.kml

* protection_zones.kml

    This is a KML file produced by the script at src/data/protection_zones.py. It contains a
    normalized set of polygons defining ground-based and coastal exclusion zones. The coastal
    exclusion zones make use of the US border definition in data/fcc/usborder.kml to bound
    the exclusion zone borders provided by the NTIA.

