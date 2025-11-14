"""SK Spot integrace."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import SKSpotCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup z config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Vytvoř sdílený coordinator
    coordinator = SKSpotCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    # Ulož coordinator do hass.data
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Nastav platformy
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Naplánuj automatické aktualizace
    coordinator.schedule_next_update()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
