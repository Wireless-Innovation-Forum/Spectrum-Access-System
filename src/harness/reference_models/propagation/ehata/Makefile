PYTHON2	?= python
PYTHON3	?= python3
SETUP	:= setup.py

all: py2 py3


py2:
	$(PYTHON2) $(SETUP)  build_ext -i
	make cleantmp

py3:
	$(PYTHON3) $(SETUP)  build_ext -i
	make cleantmp


cleantmp:
	-rm -rf build

clean:	cleantmp
	-rm -rf *.so *.pyd
