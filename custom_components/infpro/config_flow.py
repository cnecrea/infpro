"""Config flow pentru integrarea INFP."""
import voluptuous as vol
import logging
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, UPDATE_INTERVAL, DEFAULT_ORAS, LISTA_ORASE

_LOGGER = logging.getLogger(__name__)


class InfProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configurare pentru integrarea INFP."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primul pas din configurare."""
        if user_input is not None:
            # Obține numele orașului bazat pe ID-ul selectat
            oras_id = user_input["oras_id"]
            orase = {oras.split(": ")[0]: oras.split(": ")[1] for oras in LISTA_ORASE}
            oras_nume = orase.get(oras_id, "Necunoscut")

            _LOGGER.debug(
                "Utilizatorul a selectat orașul: ID=%s, Nume oraș=%s",
                oras_id,
                oras_nume,
            )

            # Conversia cheii update_interval la litere mici
            user_input = {
                "update_interval": user_input["update_interval"],
                "oras_id": oras_id,
                "oras_nume": oras_nume,
            }

            return self.async_create_entry(
                title=self.hass.data.get("translations", {}).get("config.title", "Cutremur România (INFP)"),
                data=user_input,
            )

        _LOGGER.debug("Inițializare formular pentru configurarea INFP.")

        orase = {oras.split(": ")[0]: oras.split(": ")[1] for oras in LISTA_ORASE}

        schema = vol.Schema({
            vol.Required(
                "update_interval",
                default=UPDATE_INTERVAL
            ): vol.All(vol.Coerce(int), vol.Range(min=30)),
            vol.Required(
                "oras_id",
                default=DEFAULT_ORAS
            ): vol.In(orase),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={
                "description": self.hass.data.get("translations", {}).get("config.step.user.description", "")
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Returnează fluxul de opțiuni."""
        return InfProOptionsFlow(config_entry)


class InfProOptionsFlow(config_entries.OptionsFlow):
    """Flux de opțiuni pentru integrarea INFP."""

    def __init__(self, config_entry):
        """Inițializează fluxul de opțiuni."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Pasul inițial pentru fluxul de opțiuni."""
        if user_input is not None:
            # Actualizăm numele orașului la modificarea opțiunilor
            oras_id = user_input["oras_id"]
            orase = {oras.split(": ")[0]: oras.split(": ")[1] for oras in LISTA_ORASE}
            oras_nume = orase.get(oras_id, "Necunoscut")

            _LOGGER.debug(
                "Utilizatorul a actualizat orașul: ID=%s, Nume=%s",
                oras_id,
                oras_nume,
            )

            user_input["oras_nume"] = oras_nume
            return self.async_create_entry(title="", data=user_input)

        _LOGGER.debug("Inițializare formular pentru opțiunile fluxului INFP.")

        orase = {oras.split(": ")[0]: oras.split(": ")[1] for oras in LISTA_ORASE}

        schema = vol.Schema({
            vol.Required(
                "update_interval",
                default=self.config_entry.options.get("update_interval", UPDATE_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=30)),
            vol.Required(
                "oras_id",
                default=self.config_entry.options.get("oras_id", DEFAULT_ORAS)
            ): vol.In(orase),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "description": self.hass.data.get("translations", {}).get("config.step.init.description", "")
            }
        )
