import logging
from datetime import timedelta

import aiohttp

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

URL = "http://shakemap4.infp.ro/atlas/data/event.pf"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configurează senzorul de cutremur INFP."""
    _LOGGER.debug("Inițiem configurarea senzorului Cutremur România (INFP).")
    try:
        sensor = InfpEarthquakeSensor(hass, entry)
        async_add_entities([sensor], update_before_add=True)
        _LOGGER.debug("Senzorul a fost adăugat cu succes.")

        # Intervalul curent (la fiecare load / reload)
        update_interval = timedelta(seconds=sensor._update_interval)

        # Programează actualizările periodice
        async_track_time_interval(hass, sensor.async_update, update_interval)

    except Exception as e:
        _LOGGER.error("A apărut o eroare la configurarea senzorului: %s", str(e))


class InfpEarthquakeSensor(Entity):
    """Reprezintă senzorul de cutremur INFP."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry

        # Valorile implicite
        self._state = None
        self._attributes = {}
        self._name = "Cutremur"

        # Citim intervalul din entry.options (setat de user),
        # altfel folosim DEFAULT_UPDATE_INTERVAL
        self._update_interval = entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)

        _LOGGER.debug(
            "Senzorul inițializat cu intervalul de actualizare: %s secunde",
            self._update_interval,
        )

    @property
    def unique_id(self):
        return f"{DOMAIN}_cutremur"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
            "via_device": (DOMAIN, "cutremur"),
        }

    async def async_update(self, now=None):
        """Actualizare periodică."""
        _LOGGER.debug("Actualizare senzor la interval de %s sec.", self._update_interval)

        async with aiohttp.ClientSession() as session:
            try:
                data = await self.fetch_data(session)
                parsed_data = self.parse_event_data(data)
                _LOGGER.debug("Datele au fost analizate cu succes")

                self._state = parsed_data.get("mag_ml", "Necunoscut")
                self._attributes = {
                    "ID": parsed_data.get("smevid"),
                    "Magnitudine": parsed_data.get("mag_ml"),
                    "Magnitudinea Momentului (Mw)": parsed_data.get("mag_mw"),
                    "Ora (UTC)": parsed_data.get("origin_time"),
                    "Ora locală": parsed_data.get("local_time"),
                    "Latitudine": parsed_data.get("elat"),
                    "Longitudine": parsed_data.get("elon"),
                    "Adâncime (km)": parsed_data.get("depth"),
                    "Zonă": parsed_data.get("location"),
                    "Intensitate": parsed_data.get("intensity"),
                }
                _LOGGER.debug("Starea senzorului a fost actualizată la: %s", self._state)
            except Exception as e:
                _LOGGER.error("Eroare la actualizarea datelor: %s", str(e))
                self._attributes = {"Eroare": str(e)}

    @staticmethod
    async def fetch_data(session: aiohttp.ClientSession):
        """Obține date de la URL-ul INFP."""
        _LOGGER.debug("Se încearcă preluarea datelor de la URL: %s", URL)
        async with session.get(URL) as response:
            if response.status != 200:
                error_message = f"Preluarea datelor a eșuat cu codul de status: {response.status}"
                _LOGGER.error(error_message)
                raise Exception(error_message)
            data = await response.text()
            _LOGGER.debug(
                "Datele au fost preluate cu succes (primele 100 caractere): %s",
                data[:100]
            )
            return data

    @staticmethod
    def parse_event_data(data: str):
        """Analizează datele INFP într-un dicționar (cheie=valoare)."""
        event_data = {}
        for line in data.splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                event_data[key.strip()] = value.strip()
        return event_data
