FROM ubuntu

ADD . /root

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y python-pip && \
  apt-get install -y cmake && \
  apt-get install -y libgdal-dev && \
  apt-get install -y python-gdal && \
  apt-get install -y git

RUN \
  git clone https://git.osgeo.org/gitea/geos/geos.git /geos && \
  mkdir /geos/build && \
  cd /geos/build && \
  cmake /geos && \
  make && \
  make install && \
  ldconfig


RUN \
  pip install lxml && \
  pip install numpy && \
  pip install shapely && \
  pip install pyJWT && \
  pip install cryptography && \
  pip install pykml && \
  pip install pyshp && \
  pip install ftputil && \
  pip install jsonschema && \
  pip install pyopenssl && \
  pip install mock && \
  pip install functools32 && \
  pip install psutil && \
  pip install portpicker