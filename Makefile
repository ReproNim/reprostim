# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

CONFIG_SCHEMA := src/reprostim/schemas/config.linkml.yaml
CONFIG_MODEL := src/reprostim/cli/config_model.py
LICENSE_HEADER := tools/license_header.txt

.PHONY: generate-config-model

# Generates Pydantic config model from LinkML schema.
# To force regeneration:
#   make -B generate-config-model
generate-config-model: $(CONFIG_MODEL)

$(CONFIG_MODEL): $(CONFIG_SCHEMA) $(LICENSE_HEADER)
	@cat $(LICENSE_HEADER) > $(CONFIG_MODEL)
	@printf '\n' >> $(CONFIG_MODEL)
	@gen-pydantic --extra-fields forbid $(CONFIG_SCHEMA) >> $(CONFIG_MODEL)
	@echo "Generated $(CONFIG_MODEL)"
