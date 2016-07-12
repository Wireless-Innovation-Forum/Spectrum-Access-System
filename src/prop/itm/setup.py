from distutils.core import Extension, setup

itm_module = Extension('itm', sources = ['itm.cpp', 'itm_py.cpp'])

setup(name = 'itm',
      version = '1.0',
      description = 'Longley-Rice ITM propagation model',
      ext_modules = [itm_module])

