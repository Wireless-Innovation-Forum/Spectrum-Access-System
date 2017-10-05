all:
	@echo "**** Compiling ITM Extension Module ****"
	$(MAKE) -C itm all
	@echo " "
	@echo "**** Compiling E-Hata Extension Module ****"
	$(MAKE) -C ehata all

clean:
	$(MAKE) -C itm clean
	$(MAKE) -C ehata clean

help:
	@echo "-- Help -- "
	@echo "  all:   Build both ITM and E-Hata targets."
	@echo "  clean: Remove the targets and clean temp files."
	@echo "  tests: Run"
