import logging
from datetime import timedelta
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL, DEFAULT_ORAS, LISTA_ORASE, DISPLAY_ORASE
from .json_manager import read_json, write_json  # Import funcții asincrone

_LOGGER = logging.getLogger(__name__)

# Creează o mapare inversă pentru a converti din vizual în numele original
INVERSE_DISPLAY_ORASE = {v: k for k, v in DISPLAY_ORASE.items()}


class InfproConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestionează procesul de configurare pentru Cutremur România (INFP)."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Prima etapă de configurare."""
        errors = {}
        if user_input is not None:
            _LOGGER.debug("Date primite de la utilizator: %s", user_input)
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            oras_vizual = user_input.get("oras", DISPLAY_ORASE[DEFAULT_ORAS])
            oras = INVERSE_DISPLAY_ORASE.get(oras_vizual, DEFAULT_ORAS)

            if not 10 <= update_interval <= 3600:
                errors["base"] = "interval_actualizare_invalid"
            elif oras not in LISTA_ORASE:  # Verificăm dacă orașul ales este valid
                errors["base"] = "oras_invalid"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                # Scrie datele în JSON
                try:
                    data = await read_json(self.hass, DOMAIN) or {}
                    data.update({"update_interval": update_interval, "oras": oras})
                    await write_json(self.hass, DOMAIN, data)
                    _LOGGER.debug("Date salvate în JSON: %s", data)
                except Exception as e:
                    _LOGGER.error("Eroare la scrierea JSON-ului: %s", e)
                    errors["base"] = "eroare_fisier"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._build_schema(DEFAULT_UPDATE_INTERVAL, DISPLAY_ORASE[DEFAULT_ORAS]),
                        errors=errors,
                    )

                _LOGGER.debug("Creare integrare cu opțiunile: %s", {"update_interval": update_interval, "oras": oras})
                return self.async_create_entry(
                    title="Cutremur România (INFP)",
                    data={},  # Datele de configurare pot fi lăsate goale
                    options={"update_interval": update_interval, "oras": oras},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(DEFAULT_UPDATE_INTERVAL, DISPLAY_ORASE[DEFAULT_ORAS]),
            errors=errors,
        )

    def _build_schema(self, default_interval, default_oras_vizual):
        """Construiește schema de date pentru formular."""
        orase_vizualizate = list(DISPLAY_ORASE.values())
        return vol.Schema(
            {
                vol.Required("update_interval", default=default_interval): vol.Coerce(int),
                vol.Required("oras", default=default_oras_vizual): vol.In(orase_vizualizate),
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Returnează fluxul de opțiuni."""
        return InfproOptionsFlowHandler(config_entry)


class InfproOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestionează fluxul de opțiuni."""

    def __init__(self, config_entry):
        """Inițializează fluxul de opțiuni."""
        super().__init__()  # Asigură inițializarea corectă a clasei de bază
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Procesul de reconfigurare."""
        errors = {}
        if user_input is not None:
            update_interval = user_input.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            oras_vizual = user_input.get("oras", DISPLAY_ORASE[DEFAULT_ORAS])
            oras = INVERSE_DISPLAY_ORASE.get(oras_vizual, DEFAULT_ORAS)

            if not 10 <= update_interval <= 3600:
                errors["base"] = "interval_actualizare_invalid"
            elif oras not in LISTA_ORASE:  # Verificăm dacă orașul ales este valid
                errors["base"] = "oras_invalid"
            else:
                # Citește datele existente din JSON
                try:
                    data = await read_json(self.hass, DOMAIN) or {}
                    _LOGGER.debug("Date din JSON înainte de actualizare: %s", data)
                except Exception as e:
                    _LOGGER.error("Nu s-a reușit citirea JSON-ului: %s", e)
                    data = {}

                # Actualizează datele în JSON
                data.update({"update_interval": update_interval, "oras": oras})
                try:
                    await write_json(self.hass, DOMAIN, data)
                    _LOGGER.debug("Date scrise în JSON: %s", data)
                except Exception as e:
                    _LOGGER.error("Nu s-a reușit scrierea în JSON: %s", e)
                    errors["base"] = "eroare_fisier"
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._build_schema(
                            update_interval, DISPLAY_ORASE.get(oras, oras)
                        ),
                        errors=errors,
                    )

                # Actualizează doar coordonatorul fără a dezinstala integrarea
                coordinator = (
                    self.hass.data[DOMAIN]
                    .get(self.config_entry.entry_id, {})
                    .get("coordinator")
                )
                if coordinator:
                    coordinator.update_interval = timedelta(seconds=update_interval)
                    _LOGGER.debug(
                        "Intervalul de actualizare al coordonatorului a fost actualizat la: %s secunde",
                        update_interval,
                    )
                else:
                    _LOGGER.warning(
                        "Nu s-a găsit un coordonator activ pentru actualizare."
                    )

                # Actualizează opțiunile din config_entry fără a folosi `self.config_entry` direct
                entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        options={"update_interval": update_interval, "oras": oras},
                    )
                    _LOGGER.debug(
                        "Opțiuni după actualizarea integrării: %s",
                        entry.options,
                    )

                return self.async_create_entry(title="", data={})

        try:
            data = await read_json(self.hass, DOMAIN) or {}
            current_update_interval = data.get(
                "update_interval", DEFAULT_UPDATE_INTERVAL
            )
            current_oras = data.get("oras", DEFAULT_ORAS)
        except Exception as e:
            _LOGGER.error("Nu s-a reușit citirea JSON-ului: %s", e)
            current_update_interval = DEFAULT_UPDATE_INTERVAL
            current_oras = DEFAULT_ORAS

        _LOGGER.debug(
            "Opțiunile curente din JSON: update_interval=%s, oras=%s",
            current_update_interval,
            current_oras,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self._build_schema(
                current_update_interval, DISPLAY_ORASE.get(current_oras, current_oras)
            ),
            errors=errors,
        )

    def _build_schema(self, default_interval, default_oras_vizual):
        """Construiește schema de date pentru formular."""
        orase_vizualizate = list(DISPLAY_ORASE.values())
        return vol.Schema(
            {
                vol.Required("update_interval", default=default_interval): vol.Coerce(
                    int
                ),
                vol.Required("oras", default=default_oras_vizual): vol.In(
                    orase_vizualizate
                ),
            }
        )
