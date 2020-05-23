environment := dev
subscription_id :=
auto-approve := false

ENVIRONMENTS := $(shell find ./vars -type f -name '*.tfvars' | cut -c 8- | rev | cut -c 8- | rev | paste -sd " " - | xargs)

TF_ENV_VARS :=
TF_OPTIONS :=
TF_INIT_CONF :=
TF_RUN_CONF :=

.PHONY: help
help:
	@echo "Usage: make <plan|apply|destroy> provider=azure environment=<string> subscription_id=<string> auto-approve=<true|false>"
	@echo " "
	@echo "Options:"
	@echo "  environment      The terraform input variables file name (Supported values: [$(ENVIRONMENTS)])."
	@echo "  subscription_id  Use a specific Subscription ID which should be used."
	@echo "  auto-approve     Skip interactive approval of plan before applying (Default: 'false')."
	@echo " "

configure:
    ifeq ($(filter $(environment),$(ENVIRONMENTS)),)
		$(error Environment '$(environment)' is not supported)
    endif
    TF_ENV_VARS := TF_DATA_DIR="$(CURDIR)/.terraform/$(environment)"
    TF_OPTIONS := $(TF_OPTIONS) -var="environment=$(environment)"
    TF_OPTIONS := $(TF_OPTIONS) -var="subscription_id=$(subscription_id)"
    TF_INIT_CONF := $(TF_INIT_CONF) -backend-config="$(CURDIR)/states/$(environment).tfstate"
    TF_INIT_CONF := $(TF_INIT_CONF) -var-file="$(CURDIR)/vars/$(environment).tfvars"
    TF_RUN_CONF := $(TF_RUN_CONF) -state="$(CURDIR)/states/$(environment).tfstate"
    TF_RUN_CONF := $(TF_RUN_CONF) -var-file="$(CURDIR)/vars/$(environment).tfvars"
    ifeq ($(auto-approve),true)
        TF_RUN_CONF := $(TF_RUN_CONF) -auto-approve
    endif

.PHONY: init
init:
	$(TF_ENV_VARS) terraform init $(TF_OPTIONS) $(TF_INIT_CONF)

.PHONY: package
package:
	rm -rf $(CURDIR)/function_source.zip
	for module in 'core' 'azure' ; do \
  		module_dir=$(CURDIR)/../../git-lfs-$$module ; \
  		\
		cd $$module_dir/src/main/ ; \
		zip -r $(CURDIR)/function_source.zip ./ ; \
		\
		cd $$module_dir ; \
		rm -rf .python_packages ; \
		docker run -v `pwd`:/mnt/ --entrypoint '/bin/bash' \
			mcr.microsoft.com/azure-functions/python:2.0-python3.7-appservice -c \
			"pip install -r /mnt/requirements.txt -t /mnt/.python_packages/lib/site-packages" ; \
		zip -r $(CURDIR)/function_source.zip .python_packages/lib/site-packages ; \
		rm -rf .python_packages ; \
	done

.PHONY: plan
plan: configure init package
	$(TF_ENV_VARS) terraform plan $(TF_OPTIONS) $(TF_RUN_CONF)

.PHONY: apply
apply: configure init package
	$(TF_ENV_VARS) terraform apply $(TF_OPTIONS) $(TF_RUN_CONF)

.PHONY: destroy
destroy: configure init
	$(TF_ENV_VARS) terraform destroy $(TF_OPTIONS) $(TF_RUN_CONF)
