"""API pentru integrarea INFP."""
import aiohttp
import async_timeout
import logging

from .const import URL_CUTREMUR

_LOGGER = logging.getLogger(__name__)


async def fetch_data():
    """
    Obține datele de la API-ul INFP.

    :return: Datele primite de la API sub formă de dicționar.
    """
    _LOGGER.debug("Inițializare proces de obținere a datelor de la API-ul INFP.")
    try:
        async with aiohttp.ClientSession() as session:
            # Setăm un timeout pentru cererea HTTP
            async with async_timeout.timeout(10):  # Timeout de 10 secunde
                _LOGGER.debug("Solicităm date de la URL: %s", URL_CUTREMUR)

                async with session.get(URL_CUTREMUR) as response:
                    _LOGGER.debug("Răspuns primit cu status: %s", response.status)

                    if response.status != 200:
                        raise ValueError(
                            f"HTTP error {response.status}: {response.reason}"
                        )
                    
                    data = await response.json()
                    #_LOGGER.debug("Date obținute de la API: %s", data)

                    return data

    except Exception as e:
        _LOGGER.error("Eroare la obținerea datelor de la API-ul INFP: %s", e)
        raise

