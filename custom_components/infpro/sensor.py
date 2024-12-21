import logging
from datetime import timedelta

import aiohttp

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json  # Importă funcția pentru citirea și scrierea JSON

_LOGGER = logging.getLogger(__name__)

URL = "http://shakemap4.infp.ro/atlas/data/event.pf"

# Funcția care convertește intensitatea în textul corespunzător
def intensity_to_text(intensity):
    """Convertește intensitatea numerică într-un text prietenos."""
    if intensity == "I":
        return "Neresimțit"
    elif intensity in ["II", "III"]:
        return "Slab"
    elif intensity == "IV":
        return "Ușor"
    elif intensity == "V":
        return "Moderat"
    elif intensity == "VI":
        return "Puternic"
    elif intensity == "VII":
        return "Foarte puternic"
    elif intensity == "VIII":
        return "Sever"
    elif intensity == "IX":
        return "Violeant"
    elif intensity == ["X", "XI", "XII", "XIII"]:
        return "Extrem"
    else:
        return "Necunoscut"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configurează senzorul de cutremur INFP."""
    _LOGGER.debug("Inițiem configurarea senzorului Cutremur România (INFP).")
    try:
        # Citește configurația curentă din JSON
        data = await read_json(hass, DOMAIN)
        update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Intervalul de actualizare din JSON: %s secunde", update_interval)

        # Creează instanța senzorului
        sensor = InfpEarthquakeSensor(hass, entry, update_interval)
        async_add_entities([sensor], update_before_add=True)
        _LOGGER.debug("Senzorul a fost adăugat cu succes.")

        # Programează actualizările periodice utilizând coordonatorul dinamic
        sensor.set_update_interval(update_interval)

    except Exception as e:
        _LOGGER.error("A apărut o eroare la configurarea senzorului: %s", str(e))


class InfpEarthquakeSensor(Entity):
    """Reprezintă senzorul de cutremur INFP."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, update_interval: int):
        self.hass = hass
        self.entry = entry
        self._update_interval = update_interval
        self._state = None
        self._attributes = {}
        self._name = "Cutremur"
        self._update_task = None

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
        _LOGGER.debug("Actualizare senzor la interval de %s secunde.", self._update_interval)

        async with aiohttp.ClientSession() as session:
            try:
                # Preluăm conținutul fișierului
                raw_data = await self.fetch_data(session)
                # Parsăm datele utile
                parsed_data = self.parse_event_data(raw_data)
                _LOGGER.debug("Datele au fost analizate cu succes.")

                # Exemplu: Magnitudinea ML devine `state` al senzorului
                self._state = parsed_data.get("mag_ml", "Necunoscut")

                intensity = parsed_data.get("intensity", "I")
                intensity_text = intensity_to_text(intensity)  # Convertim intensitatea în text

                self._attributes = {
                    "ID": parsed_data.get("smevid"),
                    "Magnitudine": self._state,
                    "Magnitudinea Momentului (Mw)": parsed_data.get("mag_mw"),
                    "Ora locală": parsed_data.get("local_time"),
                    "Latitudine": parsed_data.get("elat"),
                    "Longitudine": parsed_data.get("elon"),
                    "Adâncime (km)": parsed_data.get("depth"),
                    "Zonă": parsed_data.get("location"),
                    "Intensitate": intensity_text,  # Afișăm intensitatea în text
                }

                _LOGGER.debug("Starea senzorului a fost actualizată la: %s", self._state)
            except Exception as e:
                _LOGGER.error("Eroare la actualizarea datelor: %s", str(e))
                self._attributes = {"Eroare": str(e)}

    def set_update_interval(self, update_interval: int):
        """Setează intervalul de actualizare."""
        if self._update_task:
            self._update_task()  # Dezactivează sarcina existentă

        self._update_interval = update_interval
        self._update_task = async_track_time_interval(
            self.hass, self.async_update, timedelta(seconds=update_interval)
        )
        _LOGGER.debug(
            "Intervalul de actualizare a fost setat la: %s secunde.", update_interval
        )

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
            _LOGGER.debug("Datele au fost preluate cu succes.")
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
