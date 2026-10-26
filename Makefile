
CONFIG_SCHEMA := src/reprostim/schemas/config.linkml.yaml
CONFIG_MODEL := src/reprostim/cli/config_model.py

.PHONY: generate-config-model

# Generates Pydantic config model from LinkML schema
# To force generation manually use:
#      make -B generate-config-model
generate-config-model: $(CONFIG_MODEL)

$(CONFIG_MODEL): $(CONFIG_SCHEMA)
	gen-pydantic --extra-fields forbid $(CONFIG_SCHEMA) > $(CONFIG_MODEL)
