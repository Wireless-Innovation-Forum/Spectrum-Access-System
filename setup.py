from distutils.core import setup
from pathlib import Path

from setuptools import find_packages


HARNESS_PATH = str(Path('src', 'harness'))


setup(name='DPA Calculator',
      version='1.0',
      description='Finds DPA neighborhood distances around a receive antenna',
      author='Nicholas Papadopoulos',
      package_dir={'': HARNESS_PATH},
      packages=find_packages(HARNESS_PATH, exclude='testcases'),
      )
