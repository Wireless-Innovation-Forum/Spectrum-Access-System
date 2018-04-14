This directory contains data files from the NTIA defining protection
geometries for federal incumbent protection in the 3.5GHz band.
Copyright on data files is by their creators.


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

* DPA_xx_yyyy.kml

    The latest DPA KML file defining the coastal DPAs.
    
* usborder.kmz

    This is a KMZ file defining the US border. 
    Used only for simulation and benchmark purposes.

* UrbanAreas_3601.kmz
    
    This is a KMZ file defining the US urban areas as provided by the Census bureau. 
    Used only for simulation and benchmark purposes.
    
