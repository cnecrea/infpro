import json
import os
import logging
import aiofiles
import asyncio
from asyncio import Queue

_LOGGER = logging.getLogger(__name__)

# Coadă pentru operațiuni JSON
_write_queue = Queue()

def get_json_path(hass, domain):
    """Returnează calea către fișierul JSON."""
    return os.path.join(hass.config.path("custom_components"), domain, f"{domain}_data.json")

async def ensure_json_exists(hass, domain, default_data):
    """Creează fișierul JSON dacă nu există, cu date implicite."""
    path = get_json_path(hass, domain)
    if not os.path.exists(path):
        _LOGGER.debug("Fișierul JSON nu există. Creăm un fișier nou cu datele implicite.")
        try:
            async with aiofiles.open(path, mode="w") as file:
                await file.write(json.dumps(default_data, indent=4))
            _LOGGER.debug("Fișierul JSON a fost creat cu datele: %s", default_data)
        except Exception as e:
            _LOGGER.error("Nu s-a reușit crearea fișierului JSON: %s", e)
            raise

async def read_json(hass, domain):
    """Citește datele din JSON asincron."""
    path = get_json_path(hass, domain)
    if not os.path.exists(path):
        _LOGGER.warning("Fișierul JSON nu există. Asigurați-vă că este creat.")
        return {}
    try:
        async with aiofiles.open(path, mode="r") as file:
            content = await file.read()
            if not content.strip():
                _LOGGER.warning("Fișierul JSON este gol. Returnăm date goale.")
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        _LOGGER.error("Fișierul JSON este corupt: %s", e)
        return {}
    except Exception as e:
        _LOGGER.error("Nu s-a reușit citirea fișierului JSON: %s", e)
        return {}

async def write_json(hass, domain, data):
    """Adaugă o cerere de scriere în coadă."""
    await _write_queue.put((hass, domain, data))
    _LOGGER.debug("Cererea de scriere a fost adăugată în coadă: %s", data)

async def _json_writer():
    """Task dedicat pentru scrierea în JSON."""
    while True:
        hass, domain, data = await _write_queue.get()  # Așteaptă următoarea cerere
        path = get_json_path(hass, domain)
        temp_path = f"{path}.tmp"
        try:
            async with aiofiles.open(temp_path, mode="w") as file:
                await file.write(json.dumps(data, indent=4))
            os.replace(temp_path, path)  # Înlocuiește fișierul doar după scriere completă
            _LOGGER.debug("Datele au fost scrise în JSON: %s", data)
        except Exception as e:
            _LOGGER.error("Nu s-a reușit scrierea fișierului JSON: %s", e)
        finally:
            _write_queue.task_done()

async def start_json_writer():
    """Pornește task-ul de gestionare a scrierii în JSON."""
    _LOGGER.debug("Pornim procesul de gestionare a scrierii în JSON.")
    asyncio.create_task(_json_writer())
