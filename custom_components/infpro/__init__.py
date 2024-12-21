import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration via YAML (if applicable)."""
    _LOGGER.debug("async_setup called for domain %s", DOMAIN)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration via a config entry."""
    _LOGGER.debug("Setting up entry: data=%s, options=%s", entry.data, entry.options)

    # Asigură-te că `update_interval` există în opțiuni sau adaugă o valoare implicită
    if "update_interval" not in entry.options:
        _LOGGER.warning("Options are empty, adding default values")
        hass.config_entries.async_update_entry(
            entry,
            options={"update_interval": DEFAULT_UPDATE_INTERVAL},
        )

    update_interval = timedelta(seconds=entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL))
    _LOGGER.debug("Using update_interval: %s seconds", update_interval.total_seconds())

    # Creează un DataUpdateCoordinator pentru gestionarea actualizărilor
    hass.data.setdefault(DOMAIN, {})
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN} update coordinator",
        update_interval=update_interval,
    )
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Forward către platforma `sensor`
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    _LOGGER.debug("Unloading entry: entry_id=%s, data=%s, options=%s", entry.entry_id, entry.data, entry.options)

    # Dezinstalează platforma `sensor`
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
