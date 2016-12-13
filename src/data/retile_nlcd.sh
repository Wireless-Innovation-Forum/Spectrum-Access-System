# This script retiles the large AK and CONUS NLCD data sets into more
# manageable tiled files.

cd ../../data/nlcd/

if [ ! -d nlcd_2011_landcover_2011_edition_2014_10_10_tiles ]; then
  mkdir nlcd_2011_landcover_2011_edition_2014_10_10_tiles/
fi

gdal_retile.py -v -of EHdr -ps 6000 6000 -levels 1 -ot Byte -r near \
  -targetDir nlcd_2011_landcover_2011_edition_2014_10_10_tiles/ \
  nlcd_2011_landcover_2011_edition_2014_10_10/nlcd_2011_landcover_2011_edition_2014_10_10.img

rm -rf nlcd_2011_edition_2014_10_10_tiles/1

if [ ! -d ak_nlcd_2011_landcover_1_15_15_tiles ]; then
  mkdir ak_nlcd_2011_landcover_1_15_15_tiles
fi

gdal_retile.py -v -of EHdr -ps 5000 5000 -levels 1 -ot Byte -r near \
  -targetDir ak_nlcd_2011_landcover_1_15_15_tiles/ \
  ak_nlcd_2011_landcover_1_15_15.img

rm -rf ak_nlcd_2011_landcover_1_15_15_tiles/1

