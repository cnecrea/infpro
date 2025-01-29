
import logging
import os
import aiofiles
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import Throttle

from .const import DOMAIN, ATTRIBUTION, INTENSITY_MAP, JUDETE_MAP

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configurează intrarea pentru integrarea INFP."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    oras_id = config_entry.data.get("oras_id")
    oras_nume = config_entry.data.get("oras_nume")

    # 1) Senzorul principal (CutremurSensor)
    cutremur_sensor = CutremurSensor(coordinator, oras_id, oras_nume)

    # 2) Senzorul pentru datele istorice (RecordCutremurSensor)
    record_sensor = RecordCutremurSensor(coordinator)  # Corectat: eliminată referința la `hass`

    # 3) Senzorul pentru analiza impactului în orașe (AnalizaDate)
    analiza_date_sensor = AnalizaDate(coordinator, oras_id, oras_nume)

    # Adaugă toate entitățile
    async_add_entities([cutremur_sensor, record_sensor, analiza_date_sensor])

    _LOGGER.debug(
        "Senzorii pentru INFP au fost configurați: Oras ID=%s, Oras Nume=%s. "
        "Senzorii Cutremur, RecordCutremur și AnalizaDate au fost adăugați.",
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
        self._attributes = {"status": "Date în curs de actualizare"}
        self._alerta = "Nu"

        _LOGGER.debug(
            "Senzor Cutremur inițializat: ID=%s, Nume oraș=%s",
            self._attr_unique_id,
            self._oras_nume,
        )

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
        """Actualizează datele senzorului."""
        data = self.coordinator.data

        if not data or "date_cutremur" not in data:
            _LOGGER.debug("Nu există date valide în coordinator pentru cutremur.")
            self._attributes = {"status": "Date în curs de actualizare"}
            self.async_write_ha_state()
            return

        event_data = data["date_cutremur"]

        # Actualizăm atributele senzorului cu informațiile din `date_cutremur`
        self._attributes = {
            "ID eveniment": event_data.get("smevid", "N/A"),
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

        self._alerta = "Da" if event_data.get("smevid") != self._attributes.get("ID eveniment") else "Nu"
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Returnează valoarea principală a senzorului (magnitudinea ML)."""
        data = self.coordinator.data
        if data and "date_cutremur" in data:
            event_data = data["date_cutremur"]
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
class RecordCutremurSensor(CoordinatorEntity, SensorEntity):
    """
    Senzor secundar care preia datele din `record_cutremur` din API.
    """

    def __init__(self, coordinator):
        """Inițializează senzorul."""
        super().__init__(coordinator)
        self._attr_name = "Record cutremur"
        self._attr_unique_id = f"{DOMAIN}_record_cutremur"
        self._state = "N/A"  # Magnitudinea ML
        self._attributes = {"status": "Date în curs de actualizare"}
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
        """Actualizează senzorul cu datele din API."""
        data = self.coordinator.data

        if not data or "record_cutremur" not in data:
            _LOGGER.debug("Nu există date valide pentru record_cutremur.")
            self._state = "N/A"
            self._attributes = {"status": "Date în curs de actualizare"}
            self.async_write_ha_state()
            return

        record_data = data["record_cutremur"]

        # Actualizăm atributele senzorului cu informațiile din `record_cutremur`
        self._state = record_data.get("new_mag_ml", "N/A")
        self._attributes = {
            "ID eveniment": record_data.get("new_smevid", "N/A"),
            "Magnitudine (ML)": record_data.get("new_mag_ml", "N/A"),
            "Magnitudinea Momentului (Mw)": record_data.get("mag_mw", "N/A"),
            "Ora locală": record_data.get("local_time", "N/A"),
            "Latitudine": record_data.get("elat", "N/A"),
            "Longitudine": record_data.get("elon", "N/A"),
            "Adâncime (km)": record_data.get("depth", "N/A"),
            "Zonă": record_data.get("location", "N/A"),
            "Intensitate": INTENSITY_MAP.get(record_data.get("intensity", "N/A"), "Necunoscută"),
            "attribution": ATTRIBUTION,
        }

        _LOGGER.debug(
            "RecordCutremurSensor a încărcat date: ID=%s, ML=%s",
            self._attributes.get("ID eveniment", "N/A"),
            self._state,
        )

        self._available = True
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Returnează valoarea principală a senzorului (magnitudinea ML)."""
        return self._state

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
        return "mdi:waves-arrow-up"

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
        """Actualizează datele senzorului."""
        data = self.coordinator.data

        if not data or "analiza_cutremur" not in data:
            self._attributes = {"status": "Date în curs de actualizare"}
            self._available = True  # Senzorul rămâne disponibil
            self.async_write_ha_state()
            return

        analiza = data["analiza_cutremur"]

        if not isinstance(analiza, list) or not analiza:
            self._attributes = {"status": "Date în curs de actualizare"}
            self._available = True  # Senzorul rămâne disponibil
            self.async_write_ha_state()
            return

        # Găsește datele pentru orașul specificat (oras_id)
        oras_data = next((item for item in analiza if str(item.get("oras_id")) == str(self._oras_id)), None)

        if not oras_data:
            self._attributes = {"status": "Date în curs de actualizare"}
            self._available = True  # Senzorul rămâne disponibil
            self.async_write_ha_state()
            return

        # Populează atributele senzorului cu informațiile relevante
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
