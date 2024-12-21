import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Set up from YAML (dacă ar exista). De obicei rămâne gol când 
    totul e bazat pe Config Flow.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Este apelat după crearea / reîncărcarea integrării (inclusiv la reload).
    De aici încărcăm platforma `sensor`.
    """
    _LOGGER.debug(
        "Setting up %s integration (entry_id=%s)",
        DOMAIN,
        entry.entry_id
    )
    
    # Metoda clasică pentru compatibilitate cu versiunile mai vechi
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Când se dă remove/unload. Dezinstalăm platforma `sensor`.
    """
    _LOGGER.debug("Unloading %s integration (entry_id=%s)", DOMAIN, entry.entry_id)

    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return unload_ok
