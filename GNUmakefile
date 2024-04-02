SRC_PATH ?= $(CURDIR)/src
BIN_PATH ?= $(CURDIR)/build
OUT_PATH ?= $(CURDIR)/dist

PYTHON3 ?= python3
TAR ?= tar
PANDOC ?= pandoc

SYSCONF_PLATFORM := $(shell $(PYTHON3) -c 'import sysconfig; print(sysconfig.get_platform().casefold())')
ifeq ($(SYSCONF_PLATFORM),)
  $(error Failed to determine Python3 platform configuration!)
endif

.PHONY: all build clean

all: clean build

build:
	$(PYTHON3) -m PyInstaller -Fsy -n dependencies --specpath "$(BIN_PATH)" --workpath "$(BIN_PATH)" --distpath "$(OUT_PATH)" "$(SRC_PATH)/dependencies.py"
	$(PANDOC) -o "$(OUT_PATH)/README.html" "$(CURDIR)/README.md"
	cp "$(CURDIR)/LICENSE.txt" "$(OUT_PATH)/LICENSE.txt"
	chmod 444 "$(OUT_PATH)/LICENSE.txt" "$(OUT_PATH)/README.html"
	chmod 555 "$(OUT_PATH)/dependencies"
	rm -rf "$(OUT_PATH)/dependencies.${SYSCONF_PLATFORM}.tar.xz"
	cd -- "$(OUT_PATH)" && \
	XZ_OPT=-9e $(TAR) --owner=0 --group=0 -cJvf "$(OUT_PATH)/dependencies.${SYSCONF_PLATFORM}.tar.xz" dependencies README.html LICENSE.txt

clean:
	rm -rvf "$(BIN_PATH)" "$(OUT_PATH)"
