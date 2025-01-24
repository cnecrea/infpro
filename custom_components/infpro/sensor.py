import logging
import json
import os
import aiofiles
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import Throttle

from .const import DOMAIN, ATTRIBUTION, INTENSITY_MAP, JUDETE_MAP

_LOGGER = logging.getLogger(__name__)

# Fișierul JSON pentru stocarea ultimului smevid (DEJA EXISTENT)
JSON_FILE = f"/config/custom_components/{DOMAIN}/date.json"

# Fișierul JSON NOU (record.json) în care păstrăm date suplimentare
RECORD_JSON = f"/config/custom_components/{DOMAIN}/record.json"

# Interval de scanare pentru senzorul care citește record.json
# (poți ajusta timpul după preferințe)
SCAN_INTERVAL = timedelta(seconds=30)


async def ensure_json_file_exists(filename):
    """Asigură că fișierul JSON și directorul său există."""
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            _LOGGER.debug("Directorul JSON a fost creat: %s", directory)
        except Exception as e:
            _LOGGER.error("Eroare la crearea directorului JSON: %s", e)
            return

    if not os.path.exists(filename):
        try:
            async with aiofiles.open(filename, 'w') as f:
                # Dacă e record.json, pornim cu structura { "record_cutremur": {} }
                if filename == RECORD_JSON:
                    await f.write('{"record_cutremur": {}}')
                else:
                    await f.write('{"last_smevid": null}')
            _LOGGER.debug("Fișierul JSON a fost creat: %s", filename)
        except Exception as e:
            _LOGGER.error("Eroare la crearea fișierului JSON: %s", e)


async def read_json(filename):
    """Citește conținutul unui fișier JSON în mod asincron."""
    try:
        async with aiofiles.open(filename, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except FileNotFoundError:
        _LOGGER.debug("Fișierul JSON nu există, se va crea unul nou: %s", filename)
        return {}
    except Exception as e:
        _LOGGER.error("Eroare la citirea fișierului JSON (%s): %s", filename, e)
        return {}


async def write_json(filename, data):
    """Scrie conținutul unui fișier JSON în mod asincron."""
    try:
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        _LOGGER.debug("Fișierul JSON a fost actualizat: %s", filename)
    except Exception as e:
        _LOGGER.error("Eroare la scrierea fișierului JSON (%s): %s", filename, e)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configurează intrarea pentru integrarea INFP."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    oras_id = config_entry.data.get("oras_id")
    oras_nume = config_entry.data.get("oras_nume")

    # Asigură că fișierele JSON există
    await ensure_json_file_exists(JSON_FILE)
    await ensure_json_file_exists(RECORD_JSON)

    # 1) Senzorul principal (CutremurSensor)
    cutremur_sensor = CutremurSensor(coordinator, oras_id, oras_nume)

    # 2) Senzorul nou (RecordCutremurSensor) - citește din record.json
    record_sensor = RecordCutremurSensor(hass)

    # 3) Senzorul nou (CutremurSensor)
    analiza_date_sensor = AnalizaDate(coordinator, oras_id, oras_nume)

    # Adaugă ambele entități
    async_add_entities([cutremur_sensor, record_sensor, analiza_date_sensor])

    _LOGGER.debug(
        "Senzorul Cutremur a fost configurat: Oras ID=%s, Oras Nume=%s. "
        "S-a creat și senzorul RecordCutremur.",
        oras_id,
        oras_nume,
    )



# ------------------------------------------------------------------------
# CutremurSensor
# ------------------------------------------------------------------------
class CutremurSensor(CoordinatorEntity, SensorEntity):
    """Reprezentarea senzorului principal pentru cutremure."""

    def __init__(self, coordinator, oras_id, oras_nume):
        """Inițializează senzorul."""
        super().__init__(coordinator)
        self._oras_id = oras_id
        self._oras_nume = oras_nume
        self._attr_name = "Cutremur"
        self._attr_unique_id = f"{DOMAIN}_cutremur"
        self._attributes = {}
        self._alerta = "Nu"

        self._last_smevid = None
        self._old_smevid = None

        _LOGGER.debug(
            "Senzor Cutremur inițializat: ID=%s, Nume oraș=%s",
            self._attr_unique_id,
            self._oras_nume,
        )

    async def async_added_to_hass(self):
        """Se apelează când entitatea este adăugată în Home Assistant."""
        #_LOGGER.debug("Metoda async_added_to_hass a fost apelată.")
        await super().async_added_to_hass()

        json_data = await read_json(JSON_FILE)
        self._last_smevid = json_data.get("last_smevid", None)
        self._old_smevid = json_data.get("old_smevid", None)

        def _schedule_coordinator_update():
            self.hass.async_create_task(self._async_handle_coordinator_update())

        self.async_on_remove(
            self.coordinator.async_add_listener(_schedule_coordinator_update)
        )

        await self._async_handle_coordinator_update()

    async def _async_handle_coordinator_update(self):
        """
        Această metodă este apelată de fiecare dată când coordinatorul are date noi.
        """
        #_LOGGER.debug("Metoda _async_handle_coordinator_update a fost apelată.")
        data = self.coordinator.data
        if not data or "date_cutremur" not in data:
            _LOGGER.debug("Nu există date valide în coordinator pentru cutremur.")
            return

        events = data["date_cutremur"]
        if not events or not isinstance(events, list):
            _LOGGER.debug("Structura date_cutremur este goală sau invalidă.")
            return

        first_event = events[0]
        if not first_event or not isinstance(first_event, dict):
            _LOGGER.debug("Primul element din lista date_cutremur nu este valid.")
            return

        first_key = list(first_event.keys())[0]
        event_data = first_event[first_key]

        smevid = event_data.get("smevid", "N/A")

        if self._last_smevid is None:
            self._alerta = "Nu"
            self._old_smevid = smevid
            self._last_smevid = smevid

            await self._write_smevid_json()
            _LOGGER.debug(
                "Alerta 'Nu': Prima rulare, setăm last_smevid și old_smevid la %s.",
                smevid,
            )
        else:
            if smevid != self._last_smevid:
                self._alerta = "Da"
                _LOGGER.debug(
                    "Alerta 'Da': s-a modificat ID-ul evenimentului (old=%s, new=%s).",
                    self._last_smevid,
                    smevid,
                )
                self._old_smevid = self._last_smevid
                self._last_smevid = smevid
                await self._write_smevid_json()
            else:
                self._alerta = "Nu"
                _LOGGER.debug("Alerta 'Nu': ID-ul evenimentului nu s-a schimbat (%s).", smevid)
                self._old_smevid = self._last_smevid
                await self._write_smevid_json()

        self._attributes = {
            "ID eveniment": smevid,
            "Magnitudine (ML)": event_data.get("mag_ml", "N/A"),
            "Magnitudinea Momentului (Mw)": event_data.get("mag_mw", "N/A"),
            "Ora locală": event_data.get("local_time", "N/A"),
            "Latitudine": event_data.get("elat", "N/A"),
            "Longitudine": event_data.get("elon", "N/A"),
            "Adâncime (km)": event_data.get("depth", "N/A"),
            "Zonă": event_data.get("location", "N/A"),
            "Intensitate": INTENSITY_MAP.get(event_data.get("intensity", "N/A"), "Necunoscută"),
            "Alerta": self._alerta,
            "attribution": ATTRIBUTION,
        }

        await self._update_record_file(event_data)
        self.async_write_ha_state()



    async def _write_smevid_json(self):
        """
        Salvează în date.json structura cu:
        {
        "last_smevid": self._last_smevid,
        "old_smevid": self._old_smevid
        }
        """
        to_save = {
            "last_smevid": self._last_smevid,
            "old_smevid": self._old_smevid,
        }
        await write_json(JSON_FILE, to_save)

    async def _update_record_file(self, data):
        """
        Actualizează fișierul 'record.json' sub cheia "record_cutremur"
        (logica deja existentă).
        """
        record_data = await read_json(RECORD_JSON)
        if "record_cutremur" not in record_data:
            record_data["record_cutremur"] = {}

        new_smevid = data.get("smevid", "N/A")
        new_mag_ml = data.get("mag_ml", "N/A")

        old_record = record_data["record_cutremur"]
        old_smevid = old_record.get("new_smevid")
        old_mag_ml = old_record.get("new_mag_ml")

        # Eveniment nou sau lipsă => scriem direct
        if new_mag_ml is None:
            record_data["record_cutremur"] = {
                "new_smevid": new_smevid,
                "new_mag_ml": new_mag_ml,
                "mag_mw": data.get("mag_mw", "N/A"),
                "local_time": data.get("local_time", "N/A"),
                "elat": data.get("elat", "N/A"),
                "elon": data.get("elon", "N/A"),
                "depth": data.get("depth", "N/A"),
                "location": data.get("location", "N/A"),
                "intensity": data.get("intensity", "N/A"),
            }
            await write_json(RECORD_JSON, record_data)
            _LOGGER.debug(
                "record.json: Eveniment nou (%s) înregistrat cu magnitudinea ML=%s.",
                new_smevid,
                new_mag_ml,
            )
        else:
            # Același smevid => verificăm dacă magnitudinea a crescut
            try:
                old_val = float(old_mag_ml) if old_mag_ml not in (None, "N/A") else 0.0
                new_val = float(new_mag_ml) if new_mag_ml not in (None, "N/A") else 0.0
            except ValueError:
                _LOGGER.debug(
                    "record.json: Magnitudine ML invalidă (old=%s, new=%s). Nu actualizăm.",
                    old_mag_ml,
                    new_mag_ml,
                )
                return

            if new_val > old_val:
                record_data["record_cutremur"] = {
                    "new_smevid": new_smevid,
                    "new_mag_ml": new_mag_ml,
                    "mag_mw": data.get("mag_mw", "N/A"),
                    "local_time": data.get("local_time", "N/A"),
                    "elat": data.get("elat", "N/A"),
                    "elon": data.get("elon", "N/A"),
                    "depth": data.get("depth", "N/A"),
                    "location": data.get("location", "N/A"),
                    "intensity": data.get("intensity", "N/A"),
                }
                await write_json(RECORD_JSON, record_data)
                _LOGGER.debug(
                    "record.json: Magnitudine ML a crescut pentru eveniment %s: noua valoare=%s (vechi=%s).",
                    new_smevid,
                    new_mag_ml,
                    old_mag_ml,
                )
            else:
                _LOGGER.debug(
                    "record.json: ID-ul %s are aceeași/mai mică magnitudine ML (%s) față de ce era salvat (%s). Nu actualizăm.",
                    new_smevid,
                    new_mag_ml,
                    old_mag_ml,
                )

    @property
    def native_value(self):
        """Returnează valoarea principală a senzorului (magnitudinea ML)."""
        data = self.coordinator.data
        if data and "date_cutremur" in data:
            events = data["date_cutremur"]
            if events and isinstance(events, list):
                first_event = events[0]
                if first_event and isinstance(first_event, dict):
                    first_key = list(first_event.keys())[0]
                    event_data = first_event[first_key]
                    return event_data.get("mag_ml", "N/A")
        return "N/A"

    @property
    def extra_state_attributes(self):
        """Returnează atributele suplimentare pentru senzor."""
        return self._attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:waves"

    @property
    def device_info(self):
        """Informații despre dispozitiv."""
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
        }




# ------------------------------------------------------------------------
# RecordCutremurSensor
# ------------------------------------------------------------------------
class RecordCutremurSensor(SensorEntity):
    """
    Senzor secundar care citește fișierul record.json.
    Va prelua datele de sub cheia "record_cutremur".
    """

    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "Record cutremur"
        self._attr_unique_id = f"{DOMAIN}_record_cutremur"
        self._state = None  # Magnitudinea ML
        self._attributes = {}
        self._available = True

    async def async_added_to_hass(self):
        """Se apelează când entitatea este adăugată în Home Assistant."""
        # La fiecare SCAN_INTERVAL, Home Assistant va chema async_update()
        await self.async_update()

    @property
    def available(self):
        """Returnează dacă senzorul este disponibil."""
        return self._available

    @property
    def native_value(self):
        """Valoarea principală: Magnitudine (ML) din record.json."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Atribute suplimentare: toate cele din record_cutremur."""
        return self._attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:waves-arrow-up"

    @property
    def device_info(self):
        """Informații despre dispozitiv."""
        return {
            "identifiers": {(DOMAIN, "record_cutremur")},
            "name": "Record Cutremur (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme - Record",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @Throttle(SCAN_INTERVAL)  # Asigurăm un interval minim între update-uri
    async def async_update(self):
        """
        Metodă de update asincronă. Este apelată de Home Assistant periodic (cu SCAN_INTERVAL).
        Citește fișierul record.json și preia datele sub cheia "record_cutremur".
        """
        try:
            record_data = await read_json(RECORD_JSON)
            data = record_data.get("record_cutremur", {})

            if not data:
                # Dacă nu avem nimic sub record_cutremur, considerăm senzorul disponibil,
                # dar nu avem date concrete.
                self._state = None
                self._attributes = {}
                _LOGGER.debug("record_cutremur e gol. Senzor RecordCutremur nu are date.")
            else:
                # Extragem datele
                self._state = data.get("new_mag_ml", None)
                # Restul cheilor le trecem ca atribute
                self._attributes = {
                    "ID eveniment": data.get("new_smevid", "N/A"),
                    "Magnitudine (ML)": data.get("new_mag_ml", "N/A"),
                    "Magnitudinea Momentului (Mw)": data.get("mag_mw", "N/A"),
                    "Ora locală": data.get("local_time", "N/A"),
                    "Latitudine": data.get("elat", "N/A"),
                    "Longitudine": data.get("elon", "N/A"),
                    "Adâncime (km)": data.get("depth", "N/A"),
                    "Zonă": data.get("location", "N/A"),
                    "Intensitate": INTENSITY_MAP.get(data.get("intensity", "N/A"), "Necunoscută"),
                    "attribution": ATTRIBUTION,
                }
                _LOGGER.debug(
                    "RecordCutremurSensor a încărcat date: ID=%s, ML=%s",
                    self._attributes.get("ID eveniment", "N/A"),
                    self._state,
                )
            self._available = True

        except Exception as err:
            # Dacă fișierul nu poate fi citit sau apare orice eroare, marcam senzorul ca indisponibil
            self._available = False
            _LOGGER.warning(
                "RecordCutremurSensor: Eroare la citirea record.json: %s", err
            )

    @property
    def device_info(self):
        """Informații despre dispozitiv."""
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
        }



# ------------------------------------------------------------------------
# AnalizaDate
# ------------------------------------------------------------------------
class AnalizaDate(CoordinatorEntity, SensorEntity):
    """Senzor care folosește datele din analiza_cutremur."""

    def __init__(self, coordinator, oras_id, oras_nume):
        """Inițializează senzorul DateAnaliza."""
        super().__init__(coordinator)
        self._oras_id = oras_id
        self._oras_nume = oras_nume
        self._attr_name = "Analiză date"
        self._attr_unique_id = f"{DOMAIN}_analiza_date_{oras_id}"
        self._attributes = {}
        self._available = True

    async def async_added_to_hass(self):
        """Se apelează când entitatea este adăugată în Home Assistant."""
        await super().async_added_to_hass()

        def _schedule_coordinator_update():
            self.hass.async_create_task(self._async_handle_coordinator_update())

        self.async_on_remove(
            self.coordinator.async_add_listener(_schedule_coordinator_update)
        )

        await self._async_handle_coordinator_update()

    async def _async_handle_coordinator_update(self):
        data = self.coordinator.data

        if not data or "analiza_cutremur" not in data:
            self._attributes = {"status": "date indisponibile"}
            self._available = False
            self.async_write_ha_state()
            return

        analiza = data["analiza_cutremur"]

        if not isinstance(analiza, list) or not analiza:
            self._attributes = {"status": "date indisponibile"}
            self._available = False
            self.async_write_ha_state()
            return

        prima_cheie = list(analiza[0].keys())[0]

        orase = analiza[0].get(prima_cheie, [])

        if not isinstance(orase, list):
            self._attributes = {"status": "date indisponibile"}
            self._available = False
            self.async_write_ha_state()
            return

        oras_data = next((item for item in orase if str(item.get("oras_id")) == str(self._oras_id)), None)

        if not oras_data:
            self._attributes = {"status": "date indisponibile"}
            self._available = False
            self.async_write_ha_state()
            return

        self._attributes = {
            "Oraș": oras_data.get("oras", "N/A"),
            "Județ": JUDETE_MAP.get(oras_data.get("judet", "N/A"), "N/A"),
            "Distanță (km)": oras_data.get("distanta_km", "N/A"),
            "Accelerația maximă a solului": oras_data.get("pga", "N/A"),
            "Viteza maximă a solului": oras_data.get("pgv", "N/A"),
            "Intensitate": INTENSITY_MAP.get(oras_data.get("intensitate", "N/A"), "Necunoscută"),
            "Intensitatea accelerației": oras_data.get("iacc", "N/A"),
            "attribution": ATTRIBUTION,
        }
        self._available = True
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Returnează valoarea principală a senzorului (numele orașului)."""
        return self._oras_nume

    @property
    def extra_state_attributes(self):
        """Returnează atributele suplimentare pentru senzor."""
        return self._attributes

    @property
    def available(self):
        """Returnează dacă senzorul este disponibil."""
        return self._available

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:chart-bar"

    @property
    def device_info(self):
        """Informații despre dispozitiv."""
        return {
            "identifiers": {(DOMAIN, "cutremur")},
            "name": "Cutremur România (INFP)",
            "manufacturer": "Institutul Național pentru Fizica Pământului",
            "model": "Monitorizare Seisme",
            "entry_type": DeviceEntryType.SERVICE,
        }
