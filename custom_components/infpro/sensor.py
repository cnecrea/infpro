import logging
from datetime import timedelta

import aiohttp

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json  # Import funcție pentru citirea JSON

_LOGGER = logging.getLogger(__name__)

URL = "http://shakemap4.infp.ro/atlas/data/event.pf"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configurează senzorul de cutremur INFP."""
    _LOGGER.debug("Inițiem configurarea senzorului Cutremur România (INFP).")
    try:
        # Citește configurația curentă din JSON
        data = await read_json(hass, DOMAIN)
        update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Update interval from JSON: %s", update_interval)

        # Creează instanța senzorului
        sensor = InfpEarthquakeSensor(hass, entry, update_interval)
        async_add_entities([sensor], update_before_add=True)
        _LOGGER.debug("Senzorul a fost adăugat cu succes.")

        # Programează actualizările periodice
        async_track_time_interval(
            hass, sensor.async_update, timedelta(seconds=update_interval)
        )
        _LOGGER.debug("Am creat track_time_interval cu intervalul %s sec.", update_interval)
    except Exception as e:
        _LOGGER.error("A apărut o eroare la configurarea senzorului: %s", str(e))


class InfpEarthquakeSensor(Entity):
    """Reprezintă senzorul de cutremur INFP."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, update_interval):
        self.hass = hass
        self.entry = entry
        self._state = None
        self._attributes = {}
        self._name = "Cutremur"
        self._update_interval = update_interval

        _LOGGER.debug(
            "Senzorul inițializat cu intervalul de actualizare: %s secunde",
            self._update_interval,
        )

    @property
    def should_poll(self) -> bool:
        """Entitatea nu are nevoie de polling din partea HA."""
        return False

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
                # Preluăm conținutul fișierului
                raw_data = await self.fetch_data(session)
                # Parsăm datele utile
                parsed_data = self.parse_event_data(raw_data)
                _LOGGER.debug("Datele au fost analizate cu succes")

                # Exemplu: Magnitudinea ML devine `state` al senzorului
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
    async def fetch_data(session: aiohttp.ClientSession) -> str:
        """
        Obține date de la URL-ul INFP.
        Returnează conținutul fișierului .pf ca string.
        """
        _LOGGER.debug("Se încearcă preluarea datelor de la URL: %s", URL)
        async with session.get(URL) as response:
            if response.status != 200:
                error_message = f"Preluarea datelor a eșuat cu codul de status: {response.status}"
                _LOGGER.error(error_message)
                raise Exception(error_message)

            raw_data = await response.text()
            _LOGGER.debug("Datele au fost preluate")
            return raw_data

    @staticmethod
    def parse_event_data(data: str):
        """
        Analizează datele .pf într-un dicționar (cheie=valoare),
        omite orice linie care nu conține "=" sau începe cu # / [.
        """
        event_data = {}
        for line in data.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                event_data[key.strip()] = value.strip()
        return event_data
