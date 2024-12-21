import json
import os
import logging
import aiofiles

_LOGGER = logging.getLogger(__name__)

def get_json_path(hass, domain):
    """Returnează calea către fișierul JSON."""
    return hass.config.path(f"{domain}_data.json")

async def read_json(hass, domain):
    """Citește datele din JSON asincron."""
    path = get_json_path(hass, domain)
    if not os.path.exists(path):
        _LOGGER.debug("JSON file does not exist, returning empty data.")
        return {}
    try:
        async with aiofiles.open(path, mode="r") as file:
            content = await file.read()
            return json.loads(content)
    except Exception as e:
        _LOGGER.error("Failed to read JSON file: %s", e)
        return {}

async def write_json(hass, domain, data):
    """Scrie datele în JSON asincron."""
    path = get_json_path(hass, domain)
    try:
        async with aiofiles.open(path, mode="w") as file:
            await file.write(json.dumps(data, indent=4))
        _LOGGER.debug("Data written to JSON: %s", data)
    except Exception as e:
        _LOGGER.error("Failed to write JSON file: %s", e)
