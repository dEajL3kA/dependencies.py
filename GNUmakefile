SRC_PATH ?= $(CURDIR)/src
BIN_PATH ?= $(CURDIR)/build
OUT_PATH ?= $(CURDIR)/dist

PYTHON3 ?= python3
PANDOC ?= pandoc
TAR ?= $(if $(filter %BSD SunOS,$(shell uname -s)),gtar,tar)
COMPRESS ?= gzip -9
PKG_SUFFIX ?= .tar.gz

SYSCONF_PLATFORM := $(strip $(shell $(PYTHON3) -c 'import sysconfig; print(sysconfig.get_platform().casefold())'))
ifeq ($(SYSCONF_PLATFORM),)
  $(error Failed to determine Python3 platform configuration!)
endif

PKG_VERSION := $(strip $(shell $(PYTHON3) "$(SRC_PATH)/dependencies.py" --version | grep -Eo '[[:space:]][[:digit:]]\.[[:digit:]]+[[:space:]]'))
ifeq ($(PKG_VERSION),)
  $(error Failed to determine package version!)
endif

README_FILE := README.$(if $(PANDOC),html,md)
OUTPUT_FILE := dependencies-$(PKG_VERSION)-bin.$(SYSCONF_PLATFORM)$(PKG_SUFFIX)

.PHONY: all build clean

all: clean build

build:
	$(PYTHON3) -m venv --clear "$(BIN_PATH)/.pyenv"
	"$(BIN_PATH)/.pyenv/bin/python3" -m pip install -U pip wheel pyinstaller
	"$(BIN_PATH)/.pyenv/bin/python3" -m PyInstaller -Fsy -n dependencies --specpath "$(BIN_PATH)" --workpath "$(BIN_PATH)" --distpath "$(OUT_PATH)" "$(SRC_PATH)/dependencies.py"
ifneq ($(STATICX),)
	"$(BIN_PATH)/.pyenv/bin/python3" -m pip install -U staticx
	"$(BIN_PATH)/.pyenv/bin/python3" -m staticx --strip "$(OUT_PATH)/dependencies" "$(OUT_PATH)/dependencies-static"
	mv -f "$(OUT_PATH)/dependencies-static" "$(OUT_PATH)/dependencies"
endif
	cp -f "$(CURDIR)/LICENSE.txt" "$(OUT_PATH)/LICENSE.txt"
ifneq ($(PANDOC),)
	$(PANDOC) -o "$(OUT_PATH)/$(README_FILE)" "$(CURDIR)/README.md"
else
	cp -f "$(CURDIR)/README.md" "$(OUT_PATH)/$(README_FILE)"
endif
	chmod 555 "$(OUT_PATH)/dependencies"
	chmod 444 "$(OUT_PATH)/LICENSE.txt" "$(OUT_PATH)/$(README_FILE)"
	rm -rf "$(OUT_PATH)/$(OUTPUT_FILE)"
	cd -- "$(OUT_PATH)" && \
	$(TAR) --owner=0 --group=0 -I '$(COMPRESS)' -cvf "$(OUT_PATH)/$(OUTPUT_FILE)" dependencies $(README_FILE) LICENSE.txt

clean:
	rm -rf "$(BIN_PATH)" "$(OUT_PATH)"
