import logging
import asyncio
import aiohttp
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL, DISPLAY_ORASE, DISPLAY_JUDETE, DEFAULT_ORAS, LISTA_JUDET
from .json_manager import read_json, write_json
from .json_manager import start_json_writer
from .json_manager import ensure_json_exists, read_json, write_json

_LOGGER = logging.getLogger(__name__)
URL = "http://shakemap4.infp.ro/atlas/data/event.pf"


def intensity_to_text(intensity: str) -> str:
    """Transformă intensitatea numerică în text."""
    mapping = {
        "I": "Neresimțită",
        "II": "Slabă",
        "III": "Slabă",
        "IV": "Ușoară",
        "V": "Moderată",
        "VI": "Puternică",
        "VII": "Foarte puternică",
        "VIII": "Severă",
        "IX": "Violentă",
        "X": "Extremă",
        "XI": "Catastrofală",
        "XII": "Apocaliptică",
    }
    return mapping.get(intensity, "Necunoscută")

### Funcții Utilitare
async def fetch_data(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Preia datele de la un URL specific."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            _LOGGER.error(f"Eșec la preluarea datelor. Status: {response.status}")
    except Exception as e:
        _LOGGER.error(f"Eroare la accesarea URL-ului {url}: {e}")
    return None


async def fetch_cities_data(hass: HomeAssistant, event_id: str) -> Optional[Dict[str, List[Dict[str, str]]]]:
    """Preia datele despre orașe pentru un eveniment specific."""
    url = f"http://shakemap4.infp.ro/atlas/data/{event_id}/current/products/Cities_estimated.txt"
    async with aiohttp.ClientSession() as session:
        raw_data = await fetch_data(session, url)
        if raw_data and raw_data.strip():
            parsed_data = parse_cities_data(raw_data)

            # Obținem orașul salvat din configurație
            saved_city = await get_saved_city(hass)
            if saved_city:
                filtered_cities = [
                    city for city in parsed_data.get("orașe", [])
                    if city.get("Oraș", "").upper() == saved_city.upper()
                ]

                if filtered_cities:
                    return {"orașe": filtered_cities}
                else:
                    _LOGGER.warning(
                        "Orașul salvat '%s' nu a fost găsit în datele evenimentului. Se va folosi DEFAULT_ORAS: '%s'.",
                        saved_city,
                        DEFAULT_ORAS,
                    )
            
            # Dacă orașul salvat nu este găsit, folosim DEFAULT_ORAS
            default_filtered_cities = [
                city for city in parsed_data.get("orașe", [])
                if city.get("Oraș", "").upper() == DEFAULT_ORAS.upper()
            ]
            if default_filtered_cities:
                return {"orașe": default_filtered_cities}

            # Dacă nu există nici DEFAULT_ORAS în listă, logăm eroarea
            _LOGGER.error(
                "Orașul implicit '%s' nu a fost găsit în datele evenimentului. Verificați datele primite.",
                DEFAULT_ORAS,
            )
            return {"orașe": []}

        # Logăm dacă nu există date brute
        _LOGGER.error("Nu s-au găsit date despre orașe pentru evenimentul cu ID-ul %s.", event_id)
    return None


def parse_event_data(raw_data: str) -> Dict:
    """Analizează datele de la URL-ul principal."""
    return {
        line.split("=")[0].strip(): line.split("=")[1].strip()
        for line in raw_data.splitlines()
        if "=" in line
    }


def parse_cities_data(raw_data: str) -> Dict[str, List[Dict[str, str]]]:
    """Analizează datele despre orașe."""
    cities = []
    lines = raw_data.splitlines()
    for line in lines:
        if not line.strip() or line.startswith("Nr."):
            continue
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) >= 7:
            cities.append({
                "Oraș": parts[1].strip(),
                "Distanță (km)": parts[2].strip(),
                "Județ": parts[3].strip(),
                "PGA": parts[4].strip(),
                "PGV": parts[5].strip(),
                "Intensitate": parts[6].strip(),
                "Iacc": parts[7].strip() if len(parts) > 7 else "-"
            })
    return {"orașe": cities}


async def get_saved_city(hass: HomeAssistant) -> Optional[str]:
    """Obține orașul salvat din JSON."""
    data = await read_json(hass, DOMAIN) or {}
    return data.get("oras")


### Clasa InfpEarthquakeSensor
class InfpEarthquakeSensor(Entity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, update_interval: int):
        self.hass = hass
        self.entry = entry
        self._update_interval = update_interval
        self._name = "Cutremur"
        self._state = None
        self._attributes = {}
        self._last_event_id = None  # ID-ul ultimului eveniment
        self._update_task = None

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
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:earth"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
        }

    async def async_added_to_hass(self):
        """Configurează senzorul când este adăugat în Home Assistant."""
        _LOGGER.debug("(clasa InfpEarthquakeSensor) Senzorul '%s' a fost adăugat în HA și începe actualizarea.", self._name)
        self.set_update_interval(self._update_interval)
        await self.async_update()  # Actualizare inițială imediată

    async def async_update(self, now=None):
        """Actualizează datele pentru senzorul de cutremure."""
        _LOGGER.debug("Începem actualizarea pentru senzorul '%s' la momentul %s", self._name, datetime.now())
        try:
            # Obținem datele de la URL-ul principal
            async with aiohttp.ClientSession() as session:
                raw_data = await fetch_data(session, URL)

            if not raw_data:
                _LOGGER.warning("Nu s-au obținut date de la URL-ul principal.")
                self._state = "Fără date"
                self._attributes = {"Eroare": "Nu există date disponibile."}
                self.async_write_ha_state()
                return

            # Parsează datele primite
            parsed_data = parse_event_data(raw_data)
            current_event_id = parsed_data.get("smevid", "Necunoscut")
            magnitude = parsed_data.get("mag_ml", "N/A")
            intensity = parsed_data.get("intensity", "I")
            intensity_text = intensity_to_text(intensity)

            # Citim ID-ul evenimentului anterior din JSON
            json_data = await read_json(self.hass, DOMAIN) or {}
            previous_event_id = json_data.get("last_event_id")

            # Verificăm dacă este un eveniment nou
            if current_event_id != "Necunoscut" and current_event_id != previous_event_id:
                _LOGGER.debug("Eveniment nou detectat: %s (anterior: %s)", current_event_id, previous_event_id)
                alert = "Da"
            else:
                _LOGGER.debug("Nu s-a detectat un eveniment nou. ID-ul rămâne același: %s", current_event_id)
                alert = "Nu"

            # Actualizăm JSON-ul cu noul ID de eveniment
            json_data["last_event_id"] = current_event_id
            await write_json(self.hass, DOMAIN, json_data)

            # Actualizăm starea și atributele senzorului
            self._last_event_id = current_event_id
            self._state = magnitude
            self._attributes = {
                "ID eveniment": current_event_id,
                "Magnitudine (ML)": self._state,
                "Magnitudinea Momentului (Mw)": parsed_data.get("mag_mw", "N/A"),
                "Ora locală": parsed_data.get("local_time", "N/A"),
                "Latitudine": parsed_data.get("elat", "N/A"),
                "Longitudine": parsed_data.get("elon", "N/A"),
                "Adâncime (km)": parsed_data.get("depth", "N/A"),
                "Zonă": parsed_data.get("location", "N/A"),
                "Intensitate": intensity_text,
                "Alertă": alert,
            }

            _LOGGER.debug("Actualizare completă pentru senzorul '%s': %s", self._name, self._attributes)
            self.async_write_ha_state()

        except Exception as e:
            # Gestionăm erorile apărute în timpul actualizării
            _LOGGER.error("Eroare la actualizarea senzorului '%s': %s", self._name, e)
            self._attributes = {"Eroare": str(e)}
            self.async_write_ha_state()
        finally:
            _LOGGER.debug("Finalizăm actualizarea pentru senzorul '%s'", self._name)

    def set_update_interval(self, update_interval: int):
        """Setează intervalul de actualizare al senzorului."""
        if self._update_task:
            self._update_task()  # Oprim task-ul anterior
            _LOGGER.debug("(clasa InfpEarthquakeSensor) Sarcina de actualizare anterioară a fost oprită pentru '%s'.", self._name)
        self._update_interval = update_interval
        self._update_task = async_track_time_interval(
            self.hass, self.async_update, timedelta(seconds=update_interval)
        )
        _LOGGER.debug(
            "(clasa InfpEarthquakeSensor) Intervalul de actualizare pentru '%s' a fost setat la: %s secunde.",
            self._name, update_interval
        )

### Clasa InfpCityImpactSensor
class InfpCityImpactSensor(Entity):
    def __init__(self, hass: HomeAssistant, current_event_id: str, update_interval: int):
        self.hass = hass
        self._current_event_id = current_event_id
        self._update_interval = update_interval
        self._name = "Date analiză"
        self._state = None
        self._attributes = {}
        self._update_task = None

    @property
    def unique_id(self):
        return f"{DOMAIN}_date_analiza_{self._current_event_id}"

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
    def icon(self):
        return "mdi:sine-wave"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
        }

    async def async_added_to_hass(self):
        _LOGGER.debug("(clasa InfpCityImpactSensor) Senzorul '%s' a fost adăugat în HA și începe actualizarea.", self._name)
        self.set_update_interval(self._update_interval)
        await self.async_update()

    async def async_update(self, now=None):
        """Actualizează datele pentru senzorul de impact al orașelor."""
        try:
            _LOGGER.debug("Se începe actualizarea pentru ID-ul evenimentului: %s", self._current_event_id)
            cities_data = await fetch_cities_data(self.hass, self._current_event_id)

            mapping = {
                "I": "Neresimțită",
                "II": "Slabă",
                "III": "Slabă",
                "IV": "Ușoară",
                "V": "Moderată",
                "VI": "Puternică",
                "VII": "Foarte puternică",
                "VIII": "Severă",
                "IX": "Violentă",
                "X": "Extremă",
                "XI": "Catastrofală",
                "XII": "Apocaliptică",
            }

            if cities_data and "orașe" in cities_data:
                city = cities_data["orașe"][0]
                raw_city_name = city["Oraș"]
                mapped_city_name = DISPLAY_ORASE.get(raw_city_name, raw_city_name)

                # Aplicăm mapping pentru intensitate
                raw_intensity = city.get("Intensitate", "I")
                mapped_intensity = mapping.get(raw_intensity, "Necunoscută")

                # Actualizare stare și atribute
                self._state = mapped_city_name
                self._attributes = {
                    "Oraș": self._state,
                    "Județ": DISPLAY_JUDETE.get(city.get("Județ"), city.get("Județ")),
                    "Distanță (km)": city.get("Distanță (km)"),
                    "Accelerația maximă a solului": city.get("PGA"),
                    "Viteza maximă a solului": city.get("PGV"),
                    "Intensitate": mapped_intensity,
                    "Intensitatea accelerației": city.get("Iacc", "-"),
                }

                # Salvăm orașul în JSON
                json_data = await read_json(self.hass, DOMAIN) or {}
                json_data["oras"] = raw_city_name.upper()
                await write_json(self.hass, DOMAIN, json_data)

                _LOGGER.debug("Actualizare completă pentru senzorul '%s': %s", self._name, self._attributes)
            else:
                self._state = "Fără date"
                self._attributes = {"Eroare": "Nu există date disponibile pentru orașe."}
                _LOGGER.warning("Nu s-au găsit date pentru senzorul '%s'.", self._name)

            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Eroare la actualizarea senzorului '%s': %s", self._name, e)
            self._attributes = {"Eroare": str(e)}
            self.async_write_ha_state()

    def set_update_interval(self, update_interval: int):
        """Setează intervalul de actualizare al senzorului."""
        if self._update_task:
            self._update_task()  # Oprim task-ul anterior
            _LOGGER.debug("(clasa InfpCityImpactSensor) Sarcina de actualizare anterioară a fost oprită pentru '%s'.", self._name)
        self._update_interval = update_interval
        self._update_task = async_track_time_interval(
            self.hass, self.async_update, timedelta(seconds=update_interval)
        )
        _LOGGER.debug(
            "(clasa InfpCityImpactSensor) Intervalul de actualizare pentru '%s' a fost setat la: %s secunde.",
            self._name, update_interval
        )


### Funcția de setup
async def async_setup_entry(hass, entry, async_add_entities):
    """Setup senzori pentru integrarea INFP."""
    _LOGGER.debug("Inițiem configurarea senzorilor INFP.")
    default_data = {"update_interval": 180, "oras": "ALBA IULIA"}
    
    # Asigurăm că fișierul JSON există
    await ensure_json_exists(hass, DOMAIN, default_data)

    # Pornim gestionarea scrierii asincrone
    await start_json_writer()

    # Continuăm configurarea senzorilor
    data = await read_json(hass, DOMAIN) or {}
    update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)

    # Creăm senzorul principal
    earthquake_sensor = InfpEarthquakeSensor(hass, entry, update_interval)
    async_add_entities([earthquake_sensor])

    # Funcție pentru monitorizarea și crearea senzorului secundar
    async def monitor_event_and_add_city_sensor():
        try:
            max_attempts = 5
            attempts = 0

            while not earthquake_sensor._last_event_id and attempts < max_attempts:
                _LOGGER.debug("Așteptăm ID-ul evenimentului de la senzorul principal (încercarea %d).", attempts + 1)
                await asyncio.sleep(1)
                attempts += 1

            if not earthquake_sensor._last_event_id:
                _LOGGER.error("Timeout: ID-ul evenimentului nu a fost obținut după %d secunde.", max_attempts)
                return

            _LOGGER.debug("ID-ul evenimentului detectat: %s. Creăm senzorul secundar.", earthquake_sensor._last_event_id)
            city_sensor = InfpCityImpactSensor(hass, earthquake_sensor._last_event_id, update_interval)
            async_add_entities([city_sensor])

            # Adăugăm o actualizare inițială și setăm intervalul periodic
            city_sensor.set_update_interval(update_interval)
            await city_sensor.async_update()

        except Exception as e:
            _LOGGER.error("Eroare la monitorizarea senzorului secundar: %s", e)

    # Lansăm task-ul monitorizării fără să blocăm HA
    hass.loop.create_task(monitor_event_and_add_city_sensor())
