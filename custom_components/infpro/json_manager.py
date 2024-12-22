import json
import os
import logging
import aiofiles

_LOGGER = logging.getLogger(__name__)

def get_json_path(hass, domain):
    """Returnează calea către fișierul JSON."""
    return os.path.join(hass.config.path("custom_components"), domain, f"{domain}_data.json")

async def read_json(hass, domain):
    """Citește datele din JSON asincron."""
    path = get_json_path(hass, domain)
    if not os.path.exists(path):
        _LOGGER.debug("Fișierul JSON nu există, returnăm date goale.")
        return {}
    try:
        async with aiofiles.open(path, mode="r") as file:
            content = await file.read()
            return json.loads(content)
    except Exception as e:
        _LOGGER.error("Nu s-a reușit citirea fișierului JSON: %s", e)
        return {}

async def write_json(hass, domain, data):
    """Scrie datele în JSON asincron."""
    path = get_json_path(hass, domain)
    try:
        async with aiofiles.open(path, mode="w") as file:
            await file.write(json.dumps(data, indent=4))
        _LOGGER.debug("Datele au fost scrise în JSON: %s", data)
    except Exception as e:
        _LOGGER.error("Nu s-a reușit scrierea fișierului JSON: %s", e)
