# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
import sys
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
)

metamodel_version = "1.12.0"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_assignment=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        use_enum_values=True,
        strict=False,
    )


class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key: str):
        return getattr(self.root, key)

    def __getitem__(self, key: str):
        return self.root[key]

    def __setitem__(self, key: str, value):
        self.root[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta(
    {
        "default_prefix": "reprostim",
        "default_range": "string",
        "description": "Schema of the ReproStim YAML config file overriding default "
        "values of the global options and of the sub-command options.",
        "id": "https://github.com/ReproNim/reprostim/schemas/config",
        "imports": ["linkml:types"],
        "license": "MIT",
        "name": "reprostim_config",
        "prefixes": {
            "linkml": {
                "prefix_prefix": "linkml",
                "prefix_reference": "https://w3id.org/linkml/",
            },
            "reprostim": {
                "prefix_prefix": "reprostim",
                "prefix_reference": "https://github.com/ReproNim/reprostim/schemas/config/",
            },
        },
        "source_file": "src/reprostim/schemas/config.linkml.yaml",
        "title": "ReproStim config",
        "types": {
            "Duration": {
                "description": "Number of seconds as a string (e.g. "
                '"10", "10.5") or an ISO 8601 duration '
                '(e.g. "PT10S").',
                "from_schema": "https://github.com/ReproNim/reprostim/schemas/config",
                "name": "Duration",
                "pattern": "^(\\d+(\\.\\d+)?|P(?=\\d|T\\d)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+(\\.\\d+)?S)?)?)$",
                "typeof": "string",
            }
        },
    }
)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BufferPolicy(str, Enum):
    strict = "strict"
    """
    Error if buffers extend beyond video boundaries.
    """
    flexible = "flexible"
    """
    Trim buffers to fit within video boundaries.
    """


class QrMode(str, Enum):
    none = "none"
    """
    Timing based solely on acq_time and time_offset.
    """
    auto = "auto"
    """
    Use QR data if available, fall back to NTP timing.
    """
    embed_existing = "embed-existing"
    """
    Use pre-existing parsed QR JSONL files; error if missing.
    """
    parse = "parse"
    """
    Run qr-parse on-the-fly on the source video.
    """


class LayoutMode(str, Enum):
    nearby = "nearby"
    """
    Place output next to the corresponding NIfTI file.
    """
    top_stimuli = "top-stimuli"
    """
    Place output under a top-level stimuli/ directory.
    """


class OverwriteMode(str, Enum):
    skip = "skip"
    """
    Skip the scan if output already exists.
    """
    force = "force"
    """
    Remove existing file/symlink then re-inject.
    """
    always = "always"
    """
    Run split-video without an existence check.
    """
    error = "error"
    """
    Treat existing output as an error.
    """


class LockMode(str, Enum):
    yes = "yes"
    no = "no"


class ReprostimConfig(ConfiguredBaseModel):
    """
    Root of the ReproStim config file.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {
            "from_schema": "https://github.com/ReproNim/reprostim/schemas/config",
            "tree_root": True,
        }
    )

    reprostim: Optional[ReprostimGlobalConfig] = Field(
        default=None,
        description="""Global options section.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    bids_inject: Optional[BidsInjectConfig] = Field(
        default=None,
        description="""Options of the \"bids-inject\" command (config section \"bids_inject\").""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    bids_inject_sidecar: Optional[Any] = Field(
        default=None,
        description="""Options of the \"bids-inject-sidecar\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    detect_noscreen: Optional[Any] = Field(
        default=None,
        description="""Options of the \"detect-noscreen\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    echo: Optional[Any] = Field(
        default=None,
        description="""Options of the \"echo\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    list_displays: Optional[Any] = Field(
        default=None,
        description="""Options of the \"list-displays\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    monitor_displays: Optional[Any] = Field(
        default=None,
        description="""Options of the \"monitor-displays\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    qr_parse: Optional[Any] = Field(
        default=None,
        description="""Options of the \"qr-parse\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    split_video: Optional[Any] = Field(
        default=None,
        description="""Options of the \"split-video\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    timesync_stimuli: Optional[Any] = Field(
        default=None,
        description="""Options of the \"timesync-stimuli\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )
    video_audit: Optional[Any] = Field(
        default=None,
        description="""Options of the \"video-audit\" command (schema TBD, any content allowed).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimConfig"]}},
    )


class ReprostimGlobalConfig(ConfiguredBaseModel):
    """
    Global options of the main \"reprostim\" entrypoint (section \"reprostim\").
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://github.com/ReproNim/reprostim/schemas/config"}
    )

    log_level: Optional[LogLevel] = Field(
        default=LogLevel("INFO"),
        description="""Logging level (-l / --log-level).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["ReprostimGlobalConfig"],
                "ifabsent": "string(INFO)",
            }
        },
    )
    log_format: Optional[str] = Field(
        default=None,
        description="""Logging format string (-f / --log-format), see Python logging.Formatter.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["ReprostimGlobalConfig"]}},
    )


class BidsInjectConfig(ConfiguredBaseModel):
    """
    Options of the \"bids-inject\" command (section \"bids_inject\"). Every slot matches the Click option of the same parameter name.
    """

    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta(
        {"from_schema": "https://github.com/ReproNim/reprostim/schemas/config"}
    )

    videos: Optional[str] = Field(
        default=None,
        description="""Path to videos.tsv produced by video-audit (-f / --videos). Required by the command; can be provided here or on the command line.""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BidsInjectConfig"]}},
    )
    dataset: Optional[str] = Field(
        default=".",
        description="""Home directory of the BIDS dataset being injected into (-d / --dataset).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "string(.)"}
        },
    )
    recursive: Optional[bool] = Field(
        default=False,
        description="""Recurse into subdirectories to find all *_scans.tsv files (-r / --recursive).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "false"}
        },
    )
    buffer_before: Optional[Union[float, str]] = Field(
        default="0",
        description="""Extra video to include before scan onset (-b / --buffer-before). Seconds (e.g. 10 or 10.5) or ISO 8601 duration (e.g. PT10S).""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [{"range": "float"}, {"range": "Duration"}],
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(0)",
            }
        },
    )
    buffer_after: Optional[Union[float, str]] = Field(
        default="0",
        description="""Extra video to include after scan end (-a / --buffer-after). Seconds (e.g. 10 or 10.5) or ISO 8601 duration (e.g. PT10S).""",
        json_schema_extra={
            "linkml_meta": {
                "any_of": [{"range": "float"}, {"range": "Duration"}],
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(0)",
            }
        },
    )
    buffer_policy: Optional[BufferPolicy] = Field(
        default=BufferPolicy("flexible"),
        description="""Policy for buffer overflow beyond video boundaries (-p / --buffer-policy).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(flexible)",
            }
        },
    )
    time_offset: Optional[float] = Field(
        default=0.0,
        description="""Clock offset in seconds added to BIDS scan times (-t / --time-offset).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "float(0.0)"}
        },
    )
    qr: Optional[QrMode] = Field(
        default=QrMode("none"),
        description="""QR code-based timing refinement mode (-q / --qr).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(none)",
            }
        },
    )
    layout: Optional[LayoutMode] = Field(
        default=LayoutMode("nearby"),
        description="""Output file placement layout (-l / --layout).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(nearby)",
            }
        },
    )
    reprostim_timezone: Optional[str] = Field(
        default="local",
        description="""Timezone of naive ReproStim timestamps in videos.tsv (-z / --reprostim-timezone): \"local\" or an IANA name.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(local)",
            }
        },
    )
    bids_timezone: Optional[str] = Field(
        default="local",
        description="""Timezone of naive BIDS acq_time values in _scans.tsv (-Z / --bids-timezone): \"local\" or an IANA name.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(local)",
            }
        },
    )
    match: Optional[str] = Field(
        default=".*",
        description="""Regular expression matched against the filename of each scan record (-m / --match).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "string(.*)"}
        },
    )
    ignore_paths: Optional[list[str]] = Field(
        default=None,
        description="""Files, directories or glob patterns to skip, relative to the dataset directory (-i / --ignore-path, repeatable).""",
        json_schema_extra={"linkml_meta": {"domain_of": ["BidsInjectConfig"]}},
    )
    dry_run: Optional[bool] = Field(
        default=False,
        description="""Analyse only, do not write any output (-n / --dry-run).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "false"}
        },
    )
    overwrite: Optional[OverwriteMode] = Field(
        default=OverwriteMode("skip"),
        description="""Policy for handling existing output files (-w / --overwrite).""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(skip)",
            }
        },
    )
    lock: Optional[LockMode] = Field(
        default=LockMode("yes"),
        description="""Whether to acquire the videos.tsv file lock (-k / --lock). Quote the value in YAML (\"yes\"/\"no\") to avoid boolean conversion.""",
        json_schema_extra={
            "linkml_meta": {
                "domain_of": ["BidsInjectConfig"],
                "ifabsent": "string(yes)",
            }
        },
    )
    metadata_only: Optional[bool] = Field(
        default=False,
        description="""Refresh _scans.tsv/scans.json annotations for already-generated media only (-M / --metadata-only).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "false"}
        },
    )
    verbose: Optional[bool] = Field(
        default=False,
        description="""Enable verbose output (-v / --verbose).""",
        json_schema_extra={
            "linkml_meta": {"domain_of": ["BidsInjectConfig"], "ifabsent": "false"}
        },
    )


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
ReprostimConfig.model_rebuild()
ReprostimGlobalConfig.model_rebuild()
BidsInjectConfig.model_rebuild()
