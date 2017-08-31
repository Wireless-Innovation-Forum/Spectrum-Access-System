PYTHON	?= python
SETUP	:= setup.py

all:
	$(PYTHON) $(SETUP)  build_ext -i
	make cleantmp

cleantmp:
	-rm -rf build

clean:	cleantmp
	-rm -rf *.so *.pyd

