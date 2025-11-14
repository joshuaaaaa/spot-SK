"""SK Spot binary sensors."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup binary sensorů."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SKSpotTomorrowDataSensor(coordinator, entry)])


class SKSpotTomorrowDataSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor pro indikaci dostupnosti zítřejších dat."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_name = "SK Spot Tomorrow Data"
        self._attr_unique_id = f"{entry.entry_id}_tomorrow_data"

    @property
    def is_on(self) -> bool:
        """Vrať True pokud máme zítřejší data."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("tomorrow_available", False)

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        return {
            "tomorrow_records_count": len(tomorrow_prices),
            "expected_records": 96,
            "data_complete": len(tomorrow_prices) >= 90,
        }

    @property
    def icon(self):
        """Ikona."""
        if self.is_on:
            return "mdi:calendar-check"
        return "mdi:calendar-remove"
