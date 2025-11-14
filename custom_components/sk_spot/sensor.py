"""SK Spot sensor."""
from datetime import datetime, timedelta, time
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_UNIT, UNIT_MWH, UNIT_KWH

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup senzoru."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SKSpotSensor(coordinator, entry)])


class SKSpotSensor(CoordinatorEntity, SensorEntity):
    """SK Spot Price sensor."""

    _attr_name = "SK Spot Price"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_price"
        self._entry = entry
        self._unit = entry.data.get(CONF_UNIT, UNIT_MWH)

    @property
    def native_unit_of_measurement(self):
        """Jednotka měření."""
        if self._unit == UNIT_KWH:
            return "EUR/kWh"
        return "EUR/MWh"

    @property
    def native_value(self):
        """Aktuální cena."""
        if self.coordinator.data is None:
            return 0

        price = self.coordinator.data.get("current_price", 0)

        # Převod MWh -> kWh (dělit 1000)
        if self._unit == UNIT_KWH:
            return round(price / 1000, 6)

        return price

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        now = dt_util.now()
        today_date = now.date()
        tomorrow_date = today_date + timedelta(days=1)

        # Vytvoření jednoho slovníku pro dnes i zítra
        all_prices = {}

        # Přidat dnešní ceny
        for idx in range(96):
            hour = idx // 4
            minute = (idx % 4) * 15

            if idx in today_prices:
                dt = datetime.combine(today_date, time(hour, minute))
                dt = dt_util.as_local(dt_util.as_utc(dt))
                iso_time = dt.isoformat()

                price = today_prices[idx]
                if self._unit == UNIT_KWH:
                    price = round(price / 1000, 2)
                else:
                    price = round(price, 2)

                all_prices[iso_time] = price

        # Přidat zítřejší ceny - POUZE pokud jsou skutečně dostupné A je po 13:00
        # (Data se zveřejňují každý den ve 13:00)
        if tomorrow_available and tomorrow_prices and now.time() >= time(13, 0):
            for idx in range(96):
                hour = idx // 4
                minute = (idx % 4) * 15

                if idx in tomorrow_prices:
                    price = tomorrow_prices[idx]

                    dt = datetime.combine(tomorrow_date, time(hour, minute))
                    dt = dt_util.as_local(dt_util.as_utc(dt))
                    iso_time = dt.isoformat()

                    if self._unit == UNIT_KWH:
                        price = round(price / 1000, 2)
                    else:
                        price = round(price, 2)

                    all_prices[iso_time] = price

        _LOGGER.debug("Atributy obsahují %d záznamů (dnes: %d, zítra: %d, zítra dostupné: %s)",
                     len(all_prices), len(today_prices), len(tomorrow_prices), tomorrow_available)
        return all_prices
