"""Coordonator pentru integrarea INFP."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_data
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class InfProDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordonator pentru gestionarea actualizărilor de date."""

    def __init__(self, hass, update_interval):
        """Inițializează coordonatorul."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_data_coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        _LOGGER.debug(
            "INFPDataUpdateCoordinator inițializat cu un interval de actualizare de %s secunde.",
            update_interval,
        )

    async def _async_update_data(self):
        """Actualizează datele prin API."""
        _LOGGER.debug("Inițiere proces de actualizare a datelor prin API.")
        try:
            # Apelează API-ul pentru a obține date actualizate
            data = await fetch_data()
            #_LOGGER.debug("Date actualizate cu succes: %s", data)
            return data
        except Exception as err:
            _LOGGER.error(
                "Eroare la actualizarea datelor prin API: %s", err, exc_info=True
            )
            raise UpdateFailed(f"Eroare la actualizarea datelor: {err}")
