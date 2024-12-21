import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .json_manager import read_json, write_json

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configurarea integrării din YAML (dacă este cazul)."""
    _LOGGER.debug("async_setup a fost apelat pentru domeniul %s", DOMAIN)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurarea integrării dintr-o intrare de configurare."""
    _LOGGER.debug("Se configurează integrarea: data=%s, options=%s", entry.data, entry.options)

    # Citește `update_interval` din JSON
    try:
        data = await read_json(hass, DOMAIN)
        update_interval = data.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        _LOGGER.debug("Intervalul de actualizare din JSON în timpul configurării: %s secunde", update_interval)

        # Suprascrie `entry.options` cu valoarea din JSON, dacă e cazul
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

    # Dezinstalează platforma `sensor`
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        # Șterge datele asociate cu această integrare
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Integrarea a fost dezinstalată cu succes.")

    return unload_ok
