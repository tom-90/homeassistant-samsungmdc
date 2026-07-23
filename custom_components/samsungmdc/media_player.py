"""Media Player class for Samsung MDC display."""

import asyncio
import logging
import time

from samsung_mdc import MDC
from samsung_mdc.commands import MUTE, POWER
from samsung_mdc.exceptions import (
    MDCTimeoutError,
    MDCResponseError,
    NAKError,
)

from homeassistant import config_entries
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_TYPE,
    CONF_MODEL,
    CONF_UNIQUE_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DISPLAY_ID,
    CONF_SOURCE_NAMES,
    DOMAIN,
    SOURCE_NONE,
)

from .base_entity import SamsungMDCBaseEntity
from .coordinator import MDCUpdateCoordinator
from .source_map import build_source_maps

_LOGGER = logging.getLogger(__name__)

# Connection retry settings (per Samsung MDC documentation)
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # Samsung spec: retry every 2 seconds
POWER_ON_SOCKET_RECONNECT_TIME = (
    10  # Samsung spec: must re-connect socket after 10 sec for power on
)
POWER_ON_CHECK_INTERVAL = 3  # Check every 3 seconds after socket reconnect
MAX_POWER_ON_CHECKS = 10  # Try for up to 30 more seconds (10 * 3)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Samsung MDC media player from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The configuration entry for this integration.
        async_add_entities: Callback to add entities to Home Assistant.
    """
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: MDCUpdateCoordinator = data["coordinator"]
    device_unique_id = data["unique_base"]
    device_model = entry.data.get(CONF_MODEL, "Unknown")
    source_overrides = entry.options.get(CONF_SOURCE_NAMES, {})

    unique_id = f"{device_unique_id}-media_player"

    async_add_entities(
        [
            SamsungMDCMediaPlayer(
                coordinator,
                name=None,
                model=device_model,
                unique_id=unique_id,
                device_unique_id=device_unique_id,
                source_overrides=source_overrides,
            )
        ],
        True,
    )


class SamsungMDCMediaPlayer(SamsungMDCBaseEntity, MediaPlayerEntity):
    """Samsung MDC screen represented as a media_player."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_icon = "mdi:television"
    _attr_supported_features = (
        MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.VOLUME_STEP
    )

    def __init__(
        self,
        coordinator: MDCUpdateCoordinator,
        *,
        name: str | None,
        model: str | None,
        unique_id: str,
        device_unique_id: str,
        source_overrides: dict[str, str] | None = None,
    ) -> None:
        """Initialize the media player, building the source maps with any overrides applied."""
        super().__init__(
            coordinator,
            name=name,
            model=model,
            unique_id=unique_id,
            device_unique_id=device_unique_id,
        )
        self._enum_to_name, self._name_to_enum = build_source_maps(source_overrides)

    # ----- State mapping from coordinator cache -----
    @property
    def state(self):
        """Return the current power state of the display.

        Returns
        -------
        MediaPlayerState
            MediaPlayerState.ON if powered on, MediaPlayerState.OFF if powered off, or None if unavailable.
        """
        data = self.coordinator.data or {}
        if not data:
            return None

        return (
            MediaPlayerState.ON
            if self.coordinator.effective_power_state
            else MediaPlayerState.OFF
        )

    @property
    def is_volume_muted(self) -> bool | None:
        """Return True if the display volume is muted, False if not, or None if unavailable."""
        data = self.coordinator.data or {}
        return data.get("muted")

    @property
    def volume_level(self) -> float | None:
        """Return the current volume level as a float between 0.0 and 1.0, or None if unavailable."""
        data = self.coordinator.data or {}
        vol = data.get("volume")
        if vol is None:
            return None
        # Normalize to 0.0-1.0 (adapt to your device’s range)
        return max(0.0, min(1.0, vol / 100.0))

    @property
    def source_list(self):
        """Return the list of available input sources for the display."""
        return list(self._enum_to_name.values())

    @property
    def source(self):
        """Return the current input source of the display."""
        data = self.coordinator.data or {}
        src_enum = data.get("input")
        return self._enum_to_name.get(src_enum, SOURCE_NONE)

    # ----- Commands delegate to coordinator (which handles retries) -----
    async def async_turn_on(self) -> None:
        """Turn on the Samsung MDC display."""
        await self.coordinator.async_power_on()

    async def async_turn_off(self) -> None:
        """Turn off the Samsung MDC display."""
        await self.coordinator.async_power_off()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the display volume level.

        Args:
            volume: The desired volume level as a float between 0.0 and 1.0.
        """
        # Convert 0.0-1.0 back to device scale
        val = round(volume * 100)
        await self.coordinator.async_execute("volume", args=[val])

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the display volume.

        Args:
            mute: True to mute, False to unmute.
        """
        await self.coordinator.async_execute("mute", args=[mute])

    async def async_select_source(self, source: str) -> None:
        """Select the input source for the display.

        Args:
            source: The name of the input source to select.

        """
        await self.coordinator.async_execute(
            "input_source", args=[self._name_to_enum[source]]
        )
