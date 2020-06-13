environment := dev
auto-approve := false

ENVIRONMENTS := $(shell find ./vars -type f -name '*.tfvars' | cut -c 8- | rev | cut -c 8- | rev | paste -sd " " - | xargs)

TF_ENV_VARS :=
TF_OPTIONS :=
TF_INIT_CONF :=
TF_RUN_CONF :=

.PHONY: help
help:
	@echo "Usage: make <plan|apply|destroy> provider=self environment=<string> auto-approve=<true|false>"
	@echo " "
	@echo "Options:"
	@echo "  environment      The terraform input variables file name (Supported values: [$(ENVIRONMENTS)])."
	@echo "  auto-approve     Skip interactive approval of plan before applying (Default: 'false')."
	@echo " "

configure:
    ifeq ($(filter $(environment),$(ENVIRONMENTS)),)
		$(error Environment '$(environment)' is not supported)
    endif
    TF_ENV_VARS := TF_DATA_DIR="$(CURDIR)/.terraform/$(environment)"
    TF_OPTIONS := $(TF_OPTIONS) -var="environment=$(environment)"
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
	rm -rf $(CURDIR)/.source_code
	for module in 'core' 'self' ; do \
  		module_dir=$(CURDIR)/../../git-lfs-$$module ; \
  		\
		cd $$module_dir/src/main/ ; \
		cp -R ./ $(CURDIR)/.source_code ; \
		\
		cd $$module_dir ; \
		cat requirements.txt >> $(CURDIR)/.source_code/requirements.txt ; \
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
