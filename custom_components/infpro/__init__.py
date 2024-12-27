import logging
from datetime import timedelta
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL, DEFAULT_ORAS, LISTA_ORASE, DISPLAY_ORASE
from .json_manager import read_json, write_json, get_json_path

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configurarea integrării din YAML (dacă este cazul)."""
    _LOGGER.debug("async_setup a fost apelat pentru domeniul %s", DOMAIN)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurarea integrării dintr-o intrare de configurare."""
    _LOGGER.debug("Se configurează integrarea: data=%s, options=%s", entry.data, entry.options)

    try:
        # Citește datele din JSON sau folosește opțiunile entry
        data = await read_json(hass, DOMAIN)
        if not data:  # Dacă fișierul JSON este gol/inexistent
            data = {"update_interval": entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)}
            await write_json(hass, DOMAIN, data)  # Salvează valorile din entry în JSON
            _LOGGER.debug("Fișierul JSON a fost creat cu datele: %s", data)

        update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Intervalul de actualizare din JSON în timpul configurării: %s secunde", update_interval)

        # Actualizează direct entry.options dacă este necesar
        if entry.options.get("update_interval") != update_interval:
            hass.config_entries.async_update_entry(
                entry,
                options={"update_interval": update_interval},
            )
            _LOGGER.debug("Opțiunile au fost actualizate din JSON: %s", entry.options)

        # Salvează `update_interval` în `hass.data` pentru acces rapid
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "update_interval": update_interval
        }

        # Reconfigurează dacă există deja un `coordinator`
        if "coordinator" in hass.data[DOMAIN][entry.entry_id]:
            coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
            coordinator.update_interval = timedelta(seconds=update_interval)
            _LOGGER.debug("Intervalul de actualizare al coordinatorului a fost actualizat la %s secunde.", update_interval)
        else:
            # Creează un nou coordinator dacă nu există
            coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name=f"{DOMAIN} Update Coordinator",
                update_interval=timedelta(seconds=update_interval),
            )
            hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

        # Încarcă platformele necesare (de exemplu, `sensor`)
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
        _LOGGER.debug("Configurarea integrării a fost finalizată cu succes.")
        return True

    except Exception as e:
        _LOGGER.error("Eroare în timpul configurării: %s", e)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Dezinstalează integrarea."""
    _LOGGER.debug("Se dezinstalează integrarea: entry_id=%s, data=%s, options=%s", entry.entry_id, entry.data, entry.options)

    # Verificăm dacă există entități și le oprim
    for entity in hass.data[DOMAIN].get(entry.entry_id, {}).get("entities", []):
        if hasattr(entity, "async_will_remove_from_hass"):
            await entity.async_will_remove_from_hass()

    # Dezinstalează platforma `sensor`
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    _LOGGER.debug("Rezultatul dezinstalării platformelor: %s", unload_ok)

    if unload_ok:
        # Șterge datele asociate cu această integrare
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Integrarea a fost dezinstalată cu succes.")

        # Șterge fișierul JSON doar dacă nu mai există alte intrări pentru această integrare
        if not hass.config_entries.async_entries(DOMAIN):
            json_path = get_json_path(hass, DOMAIN)
            if os.path.exists(json_path):
                try:
                    os.remove(json_path)
                    _LOGGER.debug("Fișierul JSON %s a fost șters.", json_path)
                except Exception as e:
                    _LOGGER.error("Eroare la ștergerea fișierului JSON %s: %s", json_path, e)
        else:
            _LOGGER.debug("Fișierul JSON nu a fost șters deoarece există alte intrări active.")
    else:
        _LOGGER.error("Dezinstalarea platformelor a eșuat.")

    return unload_ok
