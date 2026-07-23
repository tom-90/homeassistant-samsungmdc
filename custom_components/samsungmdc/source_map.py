"""Mapping between Samsung MDC input source enum values and Home Assistant source names."""

from samsung_mdc.commands import INPUT_SOURCE

from .const import (
    SOURCE_AV,
    SOURCE_AV2,
    SOURCE_BNC,
    SOURCE_COMPONENT,
    SOURCE_DISPLAY_PORT_1,
    SOURCE_DISPLAY_PORT_2,
    SOURCE_DISPLAY_PORT_3,
    SOURCE_DVI,
    SOURCE_DVI_VIDEO,
    SOURCE_HD_BASE_T,
    SOURCE_HDMI1,
    SOURCE_HDMI1_PC,
    SOURCE_HDMI2,
    SOURCE_HDMI2_PC,
    SOURCE_HDMI3,
    SOURCE_HDMI3_PC,
    SOURCE_HDMI4,
    SOURCE_HDMI4_PC,
    SOURCE_INTERNAL_USB,
    SOURCE_IWB,
    SOURCE_MAGIC_INFO,
    SOURCE_MEDIA_MAGIC_INFO_S,
    SOURCE_NONE,
    SOURCE_PC,
    SOURCE_PLUG_IN_MODE,
    SOURCE_RF_TV,
    SOURCE_S_VIDEO,
    SOURCE_SCART1,
    SOURCE_TV_DTV,
    SOURCE_URL_LAUNCHER,
    SOURCE_WEB_BROWSER,
    SOURCE_WIDI_SCREEN_MIRRORING,
)

STATE = INPUT_SOURCE.INPUT_SOURCE_STATE

# Default HA-facing name for each MDC input source, keyed by the enum member's
# stable name (rather than its value or default label) so that config entry
# overrides keep working even if the default label text ever changes.
DEFAULT_SOURCE_NAMES: dict[str, str] = {
    STATE.NONE.name: SOURCE_NONE,
    STATE.S_VIDEO.name: SOURCE_S_VIDEO,
    STATE.COMPONENT.name: SOURCE_COMPONENT,
    STATE.AV.name: SOURCE_AV,
    STATE.AV2.name: SOURCE_AV2,
    STATE.SCART1.name: SOURCE_SCART1,
    STATE.DVI.name: SOURCE_DVI,
    STATE.PC.name: SOURCE_PC,
    STATE.BNC.name: SOURCE_BNC,
    STATE.DVI_VIDEO.name: SOURCE_DVI_VIDEO,
    STATE.MAGIC_INFO.name: SOURCE_MAGIC_INFO,
    STATE.HDMI1.name: SOURCE_HDMI1,
    STATE.HDMI1_PC.name: SOURCE_HDMI1_PC,
    STATE.HDMI2.name: SOURCE_HDMI2,
    STATE.HDMI2_PC.name: SOURCE_HDMI2_PC,
    STATE.DISPLAY_PORT_1.name: SOURCE_DISPLAY_PORT_1,
    STATE.DISPLAY_PORT_2.name: SOURCE_DISPLAY_PORT_2,
    STATE.DISPLAY_PORT_3.name: SOURCE_DISPLAY_PORT_3,
    STATE.RF_TV.name: SOURCE_RF_TV,
    STATE.HDMI3.name: SOURCE_HDMI3,
    STATE.HDMI3_PC.name: SOURCE_HDMI3_PC,
    STATE.HDMI4.name: SOURCE_HDMI4,
    STATE.HDMI4_PC.name: SOURCE_HDMI4_PC,
    STATE.TV_DTV.name: SOURCE_TV_DTV,
    STATE.PLUG_IN_MODE.name: SOURCE_PLUG_IN_MODE,
    STATE.HD_BASE_T.name: SOURCE_HD_BASE_T,
    STATE.MEDIA_MAGIC_INFO_S.name: SOURCE_MEDIA_MAGIC_INFO_S,
    STATE.WIDI_SCREEN_MIRRORING.name: SOURCE_WIDI_SCREEN_MIRRORING,
    STATE.INTERNAL_USB.name: SOURCE_INTERNAL_USB,
    STATE.URL_LAUNCHER.name: SOURCE_URL_LAUNCHER,
    STATE.IWB.name: SOURCE_IWB,
    STATE.WEB_BROWSER.name: SOURCE_WEB_BROWSER,
}

# enum member name (e.g. "HDMI1") -> enum member, for building override-aware maps
_NAME_TO_STATE = {member.name: member for member in STATE}


def build_source_maps(
    overrides: dict[str, str] | None = None,
) -> tuple[dict, dict[str, object]]:
    """Build the enum<->name maps used by the media player, applying user overrides.

    Args:
        overrides: Mapping of enum member name (e.g. "HDMI1") to a custom display name,
            as stored in the config entry options.

    Returns:
        Tuple of (enum_to_name, name_to_enum) dictionaries.
    """
    overrides = overrides or {}
    enum_to_name = {
        _NAME_TO_STATE[enum_name]: overrides.get(enum_name) or default_name
        for enum_name, default_name in DEFAULT_SOURCE_NAMES.items()
    }
    name_to_enum = {name: state for state, name in enum_to_name.items()}
    return enum_to_name, name_to_enum
