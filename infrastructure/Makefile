provider := None

PROVIDERS := $(shell find . -type d -maxdepth 1 | cut -c 3- | paste -sd " " - | xargs)

.PHONY: help
help:
    ifeq ($(filter $(provider),$(PROVIDERS)),)
		@echo "Usage: make (plan|apply|destroy) provider=%s"
		@echo " "
		@echo "Options:"
		@echo "  provider      The infrastructure provider name (Supported values: [$(PROVIDERS)])."
		@echo " "
    else
		$(MAKE) -C ${provider}/ $(@)
    endif

.PHONY: all
%:
    ifeq ($(filter $(provider),$(PROVIDERS)),)
		$(error Provider '$(provider)' is not supported)
    endif

	$(MAKE) -C ${provider}/ $(@)
