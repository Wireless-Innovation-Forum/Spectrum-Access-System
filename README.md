## The SAS Testing and Interoperability Repository

This repository contains code and data for testing the compliance
of Spectrum Access System (SAS) software. The SAS is defined by
the FCC in proceeding 12-354 as the system authorizing priority
access and general access to the 3550-3700MHz Citizens Broadband
Radio Service.

This repository contains procedures, documentation, and tests
for such software, and for the devices authorized by it.

To contribute, please first read the CONTRIBUTING file in the
repository for instructions.

### Data

Some of the required data is provided in folder `data/`. Scripts used to
retrieve or generate these data are in src/data/.

USGS NED Terrain and NLCD Land cover data are not provided as part of the
data/ folder, but kept instead in a separate Git repository found at:
 https://github.com/Wireless-Innovation-Forum/Common-Data

The process relies in cloning that repository, unzipping the geo data and
pointing the SAS reference models to point to those data.

See the corresponding [README.md](https://github.com/Wireless-Innovation-Forum/Common-Data/README.md)
for more details on the integration of those geo data for use with SAS.


### Code prerequisites

Note: see last section for an example of full installation.

The scripts in the SAS repository depend on local environment setup to run.
Here are packages and software needed to correctly operate the scripts.

* Python 3.7 (https://www.python.org/download/releases/3.7/)

This is the Python runtime which interprets the scripts in the
<code>src/</code> directory. It may already be running on many platforms, and
if it is not already installed, is widely available. Type the command
<code>python --version</code> to check the Python version installed on your
platform.

**NOTE**: The current code is designed to work with both Python 2.7 and 3.7.
It is recommended to only use Python 3.7 from now on (Python 2.7 support will
be removed in coming months). Currently untested with Python 3.8 and above.

* pip (https://pip.pypa.io/en/stable/installing/)

This is the Python package management system. If you have Python installed on
your system, it may already be available as well. The latest distributions of
Python come with <code>pip</code> pre-bundled so you may not need to retrieve
it separately. To check it's availability on your system run the command
<code>pip --version</code>.

* libgeos (http://trac.osgeo.org/geos/)

This binary library is needed to support Python <code>shapely</code> libraries.
It will likely need to be installed separately on your system. Platform-specific
instructions can be found at the above URL.

* lxml (http://lxml.de/installation.html)

This binary library provides the mechanism to support Python XML libraries.
It will likely need to be installed separately, and you may need to configure
platform-specific C++ building capabilities to complete the installation. It
can typically be installed with <code>pip</code>.

* libgdal (https://pypi.python.org/pypi/GDAL/ and http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)

This binary library provides geospatial data library methods used to manipulate
geographic datasets. It will likely need to be installed separately for your
platform, and you may need to configure platform-specific C++ build capabilities
to complete the installation. Source-based installation is an option. Once the
libgdal package is installed, you will need to download and install the Python
bindings for the library.

* numpy (http://www.scipy.org/scipylib/download.html)

This library provides a variety of numerics methods and Python bindings to use
them. It will likely need to be installed separately for your platform, and
may be installed as part of the SciPy packages.

* shapely (https://pypi.python.org/pypi/Shapely)

This Python library can be installed with <code>pip</code>. It provides
libraries for processing geometrical objects and shapes in Python.

* pyJWT (https://pypi.python.org/pypi/PyJWT)
* cryptography (https://pypi.python.org/pypi/cryptography)
* pykml (https://pythonhosted.org/pykml/installation.html)

This Python library can be installed with <code>pip</code>. It provides
libraries for handling KML geospatial files in Python.

* pyshp (https://github.com/GeospatialPython/pyshp)

This Python library can be installed with <code>pip</code>. It provides
libraries for handling SHP geospatial files in Python.

* ftputil (http://ftputil.sschwarzer.net/trac/wiki/Documentation)

This Python library can be installed with <code>pip</code>. It provides a
high-level interface for retrieving FTP files with Python.

* jsonschema (https://github.com/Julian/jsonschema)

This Python library can be installed with <code>pip</code>. It provides
JSON schema validation support.

* pyopenssl (https://github.com/pyca/pyopenssl)

This Python library can be installed with <code>pip</code>. It provides
support for the OpenSSL library for Python.

* mock (https://pypi.python.org/pypi/mock)

This Python library can be installed with <code>pip</code>. It provides
support for creating testing mocks.

* functools32 (https://pypi.python.org/pypi/functools32)

This Python library can be installed with <code>pip</code>. It provides
support for advanced functools such as OrderedDict and lru_cache memoization.

* psutil (https://github.com/giampaolo/psutil)

This Python library can be installed with <code>pip</code>. It provides
information on running processes and system (RAM,..).

* portpicker (https://pypi.org/project/portpicker)

This Python library can be installed with <code>pip</code>. It allows to
find unused network ports on a host.

For all these Python packages, a good way to test their installation is to
run the Python interpreter and then issue an <code>import xyz</code> command,
where <code>xyz</code> is the name of the package. Error-free import means
that the package is installed successfully.

* Security certificates, as described in
<code>src/harness/testcases/testdata/certs/README.md</code>


### Example of installation: Python3 installation using miniconda in Linux

This example uses the MiniConda environment manager.

Install miniconda from this page: https://docs.conda.io/en/latest/miniconda.html

Create a conda Python 3.7 environment named `winnf3`:

```shell
    conda create --name winnf3 python=3.7
```

Activate the environment on a command shell:

```shell
    conda activate winnf3
```

Install the required packages.

For the reference models and various libs:

```shell
    conda install numpy
    conda install shapely
    conda install gdal
    conda install lxml
    conda install jsonschema
    conda install matplotlib
    conda install cartopy
    pip install pygc
```

Additionally for the test harness:

```shell
    conda install cryptography
    pip install jwt
    pip install portpicker
    conda install pyopenssl
    conda install pycurl
    pip install psutil
```

Additionally for the data scripts:

```shell
    pip install ftputil
```
