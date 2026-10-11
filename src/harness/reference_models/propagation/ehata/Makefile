PYTHON ?= python3

.PHONY: all py3 clean cleantmp
all: py3

py3:
	$(PYTHON) setup.py build_ext --inplace
	$(MAKE) cleantmp

cleantmp:
	-rm -rf build

clean: cleantmp
	-rm -rf *.so *.pyd
