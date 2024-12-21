import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class InfproConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Cutremur România (INFP)."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """
        Prima etapă a ConfigFlow (când adaugi integrarea).
        Cere intervalul de actualizare 'update_interval'.
        """
        errors = {}

        if user_input is not None:
            _LOGGER.debug("User input received in config flow: %s", user_input)

            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)

            # Validare simplă
            if update_interval < 10 or update_interval > 3600:
                errors["base"] = "invalid_update_interval"
                _LOGGER.error("Interval invalid: %s", update_interval)

            if not errors:
                # Setăm un ID unic pentru integrare, evitând duplicatele
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                # Creăm intrarea (cu opțiunile salvate în `options`)
                return self.async_create_entry(
                    title="Cutremur România (INFP)",
                    data={},  # dacă ai alte date, pune-le aici
                    options={"update_interval": update_interval},
                )

        data_schema = vol.Schema(
            {
                vol.Required("update_interval", default=DEFAULT_UPDATE_INTERVAL): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the Options Flow."""
        return InfproOptionsFlowHandler(config_entry)


class InfproOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow pentru modificarea ulterioară a intervalului."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        _LOGGER.debug("InfproOptionsFlowHandler initialized with config_entry: %s", config_entry)

    async def async_step_init(self, user_input=None):
        """
        Ecranul de setări ulterioare (Options).
        Cere 'update_interval' și salvează în `entry.options`.
        """
        errors = {}
        if user_input is not None:
            _LOGGER.debug("User input for options flow: %s", user_input)

            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)

            if update_interval < 10 or update_interval > 3600:
                errors["base"] = "invalid_update_interval"
                _LOGGER.error("Interval invalid în OptionsFlow: %s", update_interval)
            else:
                # 1. Luăm dicționarul actual de opțiuni
                old_options = dict(self.config_entry.options)
                _LOGGER.debug("Old options before merge: %s", old_options)

                # 2. Actualizăm doar câmpurile care ne interesează
                old_options["update_interval"] = update_interval

                # 3. Îl salvăm în entry
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    options=old_options,  # punem TOT dicționarul
                )
                _LOGGER.debug("Options updated (merged) to: %s", self.config_entry.options)

                # IMPORTANT: forțează reload, astfel încât senzorul
                # să reia track_time_interval cu noua valoare
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.config_entry.entry_id)
                )

                return self.async_create_entry(title="", data={})

        # Afișăm formularul
        current_options = dict(self.config_entry.options)
        _LOGGER.debug("Current options in OptionsFlow: %s", current_options)

        data_schema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=current_options.get("update_interval", DEFAULT_UPDATE_INTERVAL),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
