import logging
from datetime import timedelta
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json, write_json  # Import funcții asincrone

_LOGGER = logging.getLogger(__name__)


class InfproConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestionează procesul de configurare pentru Cutremur România (INFP)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Prima etapă de configurare."""
        errors = {}
        if user_input is not None:
            _LOGGER.debug("Date primite de la utilizator: %s", user_input)
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            if not 10 <= update_interval <= 3600:
                errors["base"] = "interval_actualizare_invalid"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                _LOGGER.debug("Creare integrare cu opțiunile: %s", {"update_interval": update_interval})
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
        """Returnează fluxul de opțiuni."""
        return InfproOptionsFlowHandler(config_entry)


class InfproOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestionează fluxul de opțiuni."""

    def __init__(self, config_entry):
        """Inițializează fluxul de opțiuni."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Procesul de reconfigurare."""
        errors = {}
        if user_input is not None:
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            _LOGGER.debug("Date primite pentru fluxul de opțiuni: %s", user_input)

            if not 10 <= update_interval <= 3600:
                errors["base"] = "interval_actualizare_invalid"
            else:
                # Citește datele existente din JSON
                try:
                    data = await read_json(self.hass, DOMAIN)
                    _LOGGER.debug("Date din JSON înainte de actualizare: %s", data)
                except Exception as e:
                    _LOGGER.error("Nu s-a reușit citirea JSON-ului: %s", e)
                    data = {}

                # Actualizează `update_interval` în JSON
                data["update_interval"] = update_interval
                try:
                    await write_json(self.hass, DOMAIN, data)
                    _LOGGER.debug("Date scrise în JSON: %s", data)
                except Exception as e:
                    _LOGGER.error("Nu s-a reușit scrierea în JSON: %s", e)
                    errors["base"] = "eroare_fisier"

                # Actualizează doar coordonatorul fără a dezinstala integrarea
                coordinator = self.hass.data[DOMAIN].get(self.config_entry.entry_id, {}).get("coordinator")
                if coordinator:
                    coordinator.update_interval = timedelta(seconds=update_interval)
                    _LOGGER.debug("Intervalul de actualizare al coordonatorului a fost actualizat la: %s secunde", update_interval)
                else:
                    _LOGGER.warning("Nu s-a găsit un coordonator activ pentru actualizare.")

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    options={"update_interval": update_interval},
                )
                _LOGGER.debug("Opțiuni după actualizarea integrării: %s", self.config_entry.options)

                return self.async_create_entry(title="", data={})

        # Citește opțiunile curente
        try:
            data = await read_json(self.hass, DOMAIN)
            current_update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        except Exception as e:
            _LOGGER.error("Nu s-a reușit citirea JSON-ului: %s", e)
            current_update_interval = DEFAULT_UPDATE_INTERVAL

        _LOGGER.debug("Intervalul curent de actualizare din JSON: %s", current_update_interval)

        data_schema = vol.Schema(
            {vol.Required("update_interval", default=current_update_interval): vol.Coerce(int)}
        )
        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
