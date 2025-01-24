"""Integrarea INFP pentru Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, PLATFORMS
from .coordinator import InfProDataUpdateCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurează integrarea folosind un config entry."""
    _LOGGER.debug("Inițiere configurare pentru integrarea INFP.")

    # Inițializare stocare date pentru domeniu
    hass.data.setdefault(DOMAIN, {})

    # Preluare interval de actualizare
    update_interval = entry.options.get("UPDATE_INTERVAL", 30)
    _LOGGER.debug(
        "Intervalul de actualizare setat pentru coordonator: %s secunde.", update_interval
    )

    # Creare coordonator
    _LOGGER.debug("Inițializare coordonator pentru integrarea INFP.")
    coordinator = InfProDataUpdateCoordinator(
        hass, update_interval=update_interval
    )

    # Prima actualizare a datelor
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("Prima actualizare a datelor realizată cu succes.")
    except Exception as err:
        _LOGGER.error("Eroare la prima actualizare a datelor: %s", err)
        return False

    # Salvare coordonator în stocarea domeniului
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Încărcare platforme asociate
    _LOGGER.debug("Încărcare platforme: %s.", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Integrarea INFP a fost configurată cu succes.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Elimină o configurație."""
    _LOGGER.debug("Inițiere proces de dezinstalare pentru integrarea INFP.")

    # Dezinstalare platforme asociate
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Eliminare coordonator din stocare
        _LOGGER.debug(
            "Coordonatorul a fost eliminat din stocare pentru intrarea cu ID-ul: %s.",
            entry.entry_id,
        )

    _LOGGER.debug("Integrarea INFP a fost dezinstalată cu succes.")
    return unload_ok
