import logging
from datetime import timedelta

import aiohttp

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json, write_json  # asigură-te că există și write_json

_LOGGER = logging.getLogger(__name__)

URL = "http://shakemap4.infp.ro/atlas/data/event.pf"


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
    elif intensity in ["X", "XI", "XII", "XIII"]:
        return "Extrem"
    else:
        return "Necunoscut"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configurează senzorul de cutremur INFP."""
    _LOGGER.debug("Inițiem configurarea senzorului Cutremur România (INFP).")

    try:
        # 1) Citește fișierul JSON (dacă nu există, data va fi None sau {}).
        data = await read_json(hass, DOMAIN)
        if data is None:
            data = {}

        # 2) Ia opțiunea intervalului de la utilizator (din entry.options sau entry.data).
        #    Depinde cum ai implementat config_flow. Presupunem că e în entry.options.
        user_interval = entry.options.get("update_interval")
        #   Dacă folosești entry.data, ar fi: user_interval = entry.data.get("update_interval")

        # 3) Suprascrie intervalul din JSON cu cel venit de la utilizator, dacă există
        if user_interval is not None:
            data["update_interval"] = user_interval
            # 4) Scrie imediat în JSON noua valoare
            await write_json(hass, DOMAIN, data)
            _LOGGER.debug(
                "Utilizatorul a setat update_interval=%s. Am salvat în JSON.",
                user_interval
            )
        else:
            _LOGGER.debug(
                "Nu există update_interval în entry.options, se folosește valoarea din JSON (dacă există)."
            )

        # 5) Determină intervalul final de actualizare
        update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Interval final de actualizare: %s secunde", update_interval)

        # 6) Creează instanța senzorului
        sensor = InfpEarthquakeSensor(hass, entry, update_interval)
        async_add_entities([sensor])
        _LOGGER.debug("Senzorul a fost creat și adăugat în HA cu succes.")

        # 7) Setează intervalul de actualizare (pentru actualizări periodice)
        sensor.set_update_interval(update_interval)

        _LOGGER.debug("Configurarea senzorului a fost finalizată cu succes.")

    except Exception as e:
        _LOGGER.error("A apărut o eroare la configurarea senzorului: %s", str(e))


class InfpEarthquakeSensor(Entity):
    """Reprezintă senzorul de cutremur INFP."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, update_interval: int):
        self.hass = hass
        self.entry = entry
        self._update_interval = update_interval
        self._name = "Cutremur"

        # Starea și atributele senzorului
        self._state = None
        self._attributes = {}

        # Task-ul care rulează la fiecare X secunde (set_update_interval)
        self._update_task = None

        # ID-ul ultimului eveniment, stocat local (opțional, logica e mai mult pe JSON)
        self._last_event_id = None

        _LOGGER.debug(
            "Senzorul '%s' inițializat cu intervalul de actualizare: %s secunde",
            self._name, self._update_interval,
        )

    @property
    def should_poll(self) -> bool:
        """Nu folosim polling HA, ne actualizăm manual."""
        return False

    @property
    def unique_id(self):
        """ID unic pentru Home Assistant (va genera sensor.cutremur, etc.)."""
        return f"{DOMAIN}_cutremur"

    @property
    def name(self):
        """Numele entității."""
        return self._name

    @property
    def state(self):
        """Starea senzorului (de regulă magnitudinea ML)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Atribute suplimentare (intensitate, alertă, adâncime etc.)."""
        return self._attributes

    @property
    def device_info(self):
        """Info despre 'dispozitiv', folosită de HA la device registry."""
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
            "via_device": (DOMAIN, "cutremur"),
        }

    async def async_added_to_hass(self):
        """
        Se apelează automat după ce entitatea a primit un entity_id
        și a fost înregistrată în Home Assistant.
        """
        _LOGGER.debug(
            "Entitatea '%s' a fost adăugată în Home Assistant cu entity_id=%s",
            self._name, self.entity_id
        )

        # Facem un PRIM update imediat (fără să așteptăm intervalul)
        # astfel încât senzorul să aibă date încă de la început.
        self.hass.async_create_task(self.async_update())

    async def async_update(self, now=None):
        """
        Actualizare periodică a senzorului.
        Poate fi apelată și manual (din async_added_to_hass, etc.).
        """
        _LOGGER.debug(
            "Începem actualizarea senzorului '%s' la interval de %s secunde.",
            self._name, self._update_interval
        )

        async with aiohttp.ClientSession() as session:
            try:
                raw_data = await self.fetch_data(session)
                parsed_data = self.parse_event_data(raw_data)
                _LOGGER.debug("Am parsat cu succes datele de pe site INFP.")

                # Starea = magnitudinea ML
                self._state = parsed_data.get("mag_ml", "Necunoscut")

                # Convertim intensitatea numerică în text
                intensity = parsed_data.get("intensity", "I")
                intensity_text = intensity_to_text(intensity)

                # ID-ul evenimentului (smevid)
                current_event_id = parsed_data.get("smevid", "Necunoscut")

                # Citim ID-ul anterior din fișierul JSON
                json_data = await read_json(self.hass, DOMAIN)
                if json_data is None:
                    json_data = {}

                previous_id = json_data.get("last_event_id")

                # Stabilim dacă e un eveniment nou (Alerta="Da") sau nu
                if previous_id is not None:
                    if current_event_id != previous_id:
                        alerta = "Da"
                        _LOGGER.debug(
                            "Detectat eveniment NOU! (anterior=%s, nou=%s) => Alerta=Da",
                            previous_id, current_event_id
                        )
                    else:
                        alerta = "Nu"
                        _LOGGER.debug(
                            "Evenimentul nu s-a schimbat (anterior=%s, nou=%s) => Alerta=Nu",
                            previous_id, current_event_id
                        )
                else:
                    alerta = "Nu"
                    _LOGGER.debug(
                        "Nu există last_event_id în JSON (prima rulare?) => Alerta=Nu"
                    )

                # Scriem noul ID în JSON, pentru comparațiile viitoare
                json_data["last_event_id"] = current_event_id
                await write_json(self.hass, DOMAIN, json_data)
                _LOGGER.debug("Am salvat în JSON last_event_id = %s", current_event_id)

                self._last_event_id = current_event_id

                # Atributele senzorului
                self._attributes = {
                    "ID": current_event_id,
                    "Magnitudine (ML)": self._state,
                    "Magnitudinea Momentului (Mw)": parsed_data.get("mag_mw"),
                    "Ora locală": parsed_data.get("local_time"),
                    "Latitudine": parsed_data.get("elat"),
                    "Longitudine": parsed_data.get("elon"),
                    "Adâncime (km)": parsed_data.get("depth"),
                    "Zonă": parsed_data.get("location"),
                    "Intensitate": intensity_text,
                    "Alerta": alerta,
                }

                _LOGGER.debug(
                    "Senzorul '%s' a terminat actualizarea. Magnitudine=%s, Alerta=%s",
                    self._name, self._state, alerta
                )

                # Notificăm HA că starea/atributele s-au modificat
                self.async_write_ha_state()

            except Exception as e:
                _LOGGER.error("Eroare la actualizarea datelor pentru '%s': %s", self._name, str(e))
                self._attributes = {"Eroare": str(e)}
                self.async_write_ha_state()

    def set_update_interval(self, update_interval: int):
        """Setează intervalul de actualizare al senzorului."""
        if self._update_task:
            # Oprim job-ul anterior
            self._update_task()

        self._update_interval = update_interval

        # Programăm un update la fiecare X secunde
        self._update_task = async_track_time_interval(
            self.hass, self.async_update, timedelta(seconds=update_interval)
        )

        _LOGGER.debug(
            "Intervalul de actualizare pentru '%s' a fost setat la: %s secunde.",
            self._name, update_interval
        )

    @staticmethod
    async def fetch_data(session: aiohttp.ClientSession) -> str:
        """Obține date de la URL-ul INFP și returnează conținutul fișierului .pf ca string."""
        _LOGGER.debug("Se încearcă preluarea datelor de la URL: %s", URL)
        async with session.get(URL) as response:
            if response.status != 200:
                error_message = (
                    f"Preluarea datelor a eșuat cu codul de status: {response.status}"
                )
                _LOGGER.error(error_message)
                raise Exception(error_message)

            raw_data = await response.text()
            _LOGGER.debug("Datele de la URL: %s au fost preluate cu succes.", URL)
            return raw_data

    @staticmethod
    def parse_event_data(data: str):
        """
        Analizează conținutul .pf și îl transformă într-un dicționar (cheie=valoare).
        Omitem liniile care nu conțin "=" sau care încep cu # / [.
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
