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

### Code prerequisites

The scripts in the SAS repository depend on local environment setup to run.
Here are packages and software needed to correctly operate the scripts.

* Python 2.7 (https://www.python.org/download/releases/2.7/)

This is the Python runtime which interprets the scripts in the
<code>src/</code> directory. It may already be running on many platforms, and
if it is not already installed, is widely available. Type the command
<code>python --version</code> to check the Python version installed on your
platform.

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

* shapely (https://pypi.python.org/pypi/Shapely)

This Python library can be installed with <code>pip</code>. It provides libraries
for processing geometrical objects and shapes in Python.

* pykml (https://pythonhosted.org/pykml/installation.html)

This Python library can be installed with <code>pip</code>. It provides libraries
for handling KML geospatial files in Python.

* pyshp (https://github.com/GeospatialPython/pyshp)

This Python library can be installed with <code>pip</code>. It provides libraries
for handling SHP geospatial files in Python.

* ftputil (http://ftputil.sschwarzer.net/trac/wiki/Documentation)

This Python library can be installed with <code>pip</code>. It provides a
high-level interface for retrieving FTP files with Python.

* jsonschema (https://github.com/Julian/jsonschema)

This Python library can be installed with <code>pip</code>. It provides
JSON schema validation support.

* pyopenssl (https://github.com/pyca/pyopenssl)

This Python library can be installed with <code>pip</code>. It provides
support for the OpenSSL library for Python.


For all these Python packages, a good way to test their installation is to
run the Python interpreter and then issue an <code>import xyz</code> command,
where <code>xyz</code> is the name of the package. Error-free import means
that the package is installed successfully.


