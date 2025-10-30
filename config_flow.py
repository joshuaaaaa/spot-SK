"""Config flow pro SK Spot."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_UNIT, UNIT_MWH, UNIT_KWH


class SKSpotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user step."""
        if user_input is not None:
            return self.async_create_entry(title="SK Spot Price", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_UNIT, default=UNIT_MWH): vol.In({
                UNIT_MWH: "EUR/MWh",
                UNIT_KWH: "EUR/kWh"
            })
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
