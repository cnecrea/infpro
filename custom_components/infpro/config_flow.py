import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json, write_json  # Import funcții asincrone

_LOGGER = logging.getLogger(__name__)


class InfproConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Cutremur România (INFP)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Prima etapă de configurare."""
        errors = {}
        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            if not 10 <= update_interval <= 3600:
                errors["base"] = "invalid_update_interval"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                _LOGGER.debug("Creating entry with options: %s", {"update_interval": update_interval})
                return self.async_create_entry(
                    title="Cutremur România (INFP)",
                    data={},
                    options={"update_interval": update_interval},
                )

        data_schema = vol.Schema(
            {vol.Required("update_interval", default=DEFAULT_UPDATE_INTERVAL): vol.Coerce(int)}
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return InfproOptionsFlowHandler(config_entry)


class InfproOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Procesul de reconfigurare."""
        errors = {}
        if user_input is not None:
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            _LOGGER.debug("User input for options flow: %s", user_input)

            if not 10 <= update_interval <= 3600:
                errors["base"] = "invalid_update_interval"
            else:
                # Citește datele existente din JSON
                try:
                    data = await read_json(self.hass, DOMAIN)
                    _LOGGER.debug("Data from JSON before update: %s", data)
                except Exception as e:
                    _LOGGER.error("Failed to read JSON: %s", e)
                    data = {}

                # Actualizează `update_interval` în JSON
                data["update_interval"] = update_interval
                try:
                    await write_json(self.hass, DOMAIN, data)
                    _LOGGER.debug("Data written to JSON: %s", data)
                except Exception as e:
                    _LOGGER.error("Failed to write JSON: %s", e)
                    errors["base"] = "file_error"

                # Actualizează entry-ul
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    options={"update_interval": update_interval},
                )
                _LOGGER.debug("Options after async_update_entry: %s", self.config_entry.options)

                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        # Citește opțiunile curente
        try:
            data = await read_json(self.hass, DOMAIN)
            current_update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        except Exception as e:
            _LOGGER.error("Failed to read JSON: %s", e)
            current_update_interval = DEFAULT_UPDATE_INTERVAL

        _LOGGER.debug("Current update_interval in JSON: %s", current_update_interval)

        data_schema = vol.Schema(
            {vol.Required("update_interval", default=current_update_interval): vol.Coerce(int)}
        )
        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
