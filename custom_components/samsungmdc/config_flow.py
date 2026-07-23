"""Config flow for Samsung MDC."""

import ipaddress
from typing import Tuple
import logging

from samsung_mdc import MDC
from samsung_mdc.exceptions import (
    MDCTimeoutError,
    MDCResponseError,
    NAKError,
)

import voluptuous as vol
from voluptuous.schema_builder import message
from voluptuous.error import Invalid

from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIQUE_ID,
    CONF_MODEL,
)

from .const import (
    CONF_DISPLAY_ID,
    CONF_SOURCE_NAMES,
    DEFAULT_DISPLAY_ID,
    DEFAULT_NAME,
    DOMAIN,
    RESULT_CANNOT_CONNECT,
    RESULT_INV_DSPID,
    RESULT_INV_IP,
)
from .mdc_api import MdcApi
from .source_map import DEFAULT_SOURCE_NAMES

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_DISPLAY_ID, default=DEFAULT_DISPLAY_ID): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(CONF_NAME): str,
    }
)


def is_valid_ip(host: str):
    """Return True if IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        # Could be a hostname
        return len(host) > 0 and not host.isspace()


class SamsungMDCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Samsung MDC display entities."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SamsungMDCOptionsFlow()

    async def async_step_user(self, user_input):
        """Present form for user input for entering connection details."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_IP_ADDRESS]
            display_id = user_input[CONF_DISPLAY_ID]
            name = user_input.get(CONF_NAME, f"Samsung MDC ({host} #{display_id})")

            # Validate input
            if not is_valid_ip(host):
                errors["base"] = RESULT_INV_IP
            elif not (0 <= display_id <= 255):
                errors["base"] = RESULT_INV_DSPID
            else:
                # Test connection
                api = MdcApi(host, display_id)
                try:
                    try:
                        await api.async_connect()

                        model = await api.async_command(fn="model_name")
                        if not model or model == "Unknown":
                            errors["base"] = RESULT_CANNOT_CONNECT
                            await api.async_close()
                            return self.async_show_form(
                                step_id="user",
                                data_schema=SCHEMA,
                                errors=errors,
                            )
                    except NAKError:
                        # We get a NAKError only if the connection works as such
                        # But for example the Flip Pro only answers to power, volume, mute, input source and some undocumented smartview+ get/set,
                        # so in case no serial is returned, create a fake as UUID and set the model to "generic"
                        model = "generic"
    
                    # Create unique ID based on host and display ID
                    unique_id = f"{host}_{display_id}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_IP_ADDRESS: host,
                            CONF_DISPLAY_ID: display_id,
                            CONF_NAME: name,
                            CONF_MODEL: model,
                            CONF_TYPE: "MDC",
                            CONF_UNIQUE_ID: unique_id,
                        },
                    )
                except Exception as ex:
                    _LOGGER.error("Cannot connect to Samsung MDC display: %s", ex)
                    errors["base"] = RESULT_CANNOT_CONNECT
                    raise
                finally:
                    await api.async_close()

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA,
            errors=errors,
        )


class SamsungMDCOptionsFlow(config_entries.OptionsFlow):
    """Options flow allowing the input source names to be customized."""

    async def async_step_init(self, user_input=None):
        """Show a form with an editable name for every input source."""
        current = self.config_entry.options.get(CONF_SOURCE_NAMES, {})

        if user_input is not None:
            source_names = {
                enum_name: value.strip()
                for enum_name, value in user_input.items()
                if value and value.strip() and value.strip() != DEFAULT_SOURCE_NAMES[enum_name]
            }
            return self.async_create_entry(data={CONF_SOURCE_NAMES: source_names})

        schema = {
            vol.Optional(
                enum_name, default=current.get(enum_name, default_name)
            ): str
            for enum_name, default_name in DEFAULT_SOURCE_NAMES.items()
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
