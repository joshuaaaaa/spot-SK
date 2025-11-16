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
    async_add_entities([
        SKSpotSensor(coordinator, entry),
        SKSpotCurrentRankSensor(coordinator, entry),
        SKSpotDailyMinSensor(coordinator, entry),
        SKSpotDailyMaxSensor(coordinator, entry),
        SKSpotDailyAverageSensor(coordinator, entry),
    ])


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


class SKSpotCurrentRankSensor(CoordinatorEntity, SensorEntity):
    """Sensor zobrazující ranking aktuálního bloku (1=nejlevnější, 96=nejdražší)."""

    _attr_name = "SK Spot Current Rank"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:podium"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_current_rank"
        self._entry = entry

    @property
    def native_unit_of_measurement(self):
        """Jednotka měření."""
        return None

    @property
    def native_value(self):
        """Aktuální ranking (1-96)."""
        if self.coordinator.data is None:
            return None

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return None

        # Zjisti aktuální index
        now = dt_util.now()
        current_hour = now.hour
        current_minute = now.minute
        current_idx = (current_hour * 4) + (current_minute // 15)

        if current_idx not in today_prices:
            return None

        current_price = today_prices[current_idx]

        # Spočítej kolik bloků má nižší cenu (standard ranking)
        # Pokud je více bloků se stejnou cenou, všechny mají stejný rank
        lower_count = sum(1 for price in today_prices.values() if price < current_price)

        # Rank je počet bloků s nižší cenou + 1
        return lower_count + 1

    @property
    def extra_state_attributes(self):
        """Atributy s rankingy všech bloků."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        now = dt_util.now()
        today_date = now.date()
        tomorrow_date = today_date + timedelta(days=1)

        attrs = {}

        # Rankingy pro dnes
        if today_prices:
            today_rankings = {}
            for idx, price in today_prices.items():
                # Standard ranking: spočítej kolik bloků má nižší cenu
                rank = sum(1 for p in today_prices.values() if p < price) + 1

                hour = idx // 4
                minute = (idx % 4) * 15
                dt = datetime.combine(today_date, time(hour, minute))
                dt = dt_util.as_local(dt_util.as_utc(dt))
                iso_time = dt.isoformat()
                today_rankings[iso_time] = rank

            attrs["today_rankings"] = today_rankings

        # Rankingy pro zítra (pokud jsou dostupné)
        if tomorrow_available and tomorrow_prices and now.time() >= time(13, 0):
            tomorrow_rankings = {}
            for idx, price in tomorrow_prices.items():
                # Standard ranking: spočítej kolik bloků má nižší cenu
                rank = sum(1 for p in tomorrow_prices.values() if p < price) + 1

                hour = idx // 4
                minute = (idx % 4) * 15
                dt = datetime.combine(tomorrow_date, time(hour, minute))
                dt = dt_util.as_local(dt_util.as_utc(dt))
                iso_time = dt.isoformat()
                tomorrow_rankings[iso_time] = rank

            attrs["tomorrow_rankings"] = tomorrow_rankings

        return attrs


class SKSpotDailyMinSensor(CoordinatorEntity, SensorEntity):
    """Sensor zobrazující minimální cenu dnes."""

    _attr_name = "SK Spot Daily Min"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:arrow-down-bold"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_min"
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
        """Minimální cena dnes."""
        if self.coordinator.data is None:
            return None

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return None

        min_price = min(today_prices.values())

        if self._unit == UNIT_KWH:
            return round(min_price / 1000, 6)

        return round(min_price, 2)

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return {}

        min_price = min(today_prices.values())
        min_idx = [idx for idx, price in today_prices.items() if price == min_price][0]

        now = dt_util.now()
        today_date = now.date()

        hour = min_idx // 4
        minute = (min_idx % 4) * 15
        dt = datetime.combine(today_date, time(hour, minute))
        dt = dt_util.as_local(dt_util.as_utc(dt))

        return {
            "time": dt.isoformat(),
            "interval_index": min_idx,
        }


class SKSpotDailyMaxSensor(CoordinatorEntity, SensorEntity):
    """Sensor zobrazující maximální cenu dnes."""

    _attr_name = "SK Spot Daily Max"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:arrow-up-bold"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_max"
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
        """Maximální cena dnes."""
        if self.coordinator.data is None:
            return None

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return None

        max_price = max(today_prices.values())

        if self._unit == UNIT_KWH:
            return round(max_price / 1000, 6)

        return round(max_price, 2)

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return {}

        max_price = max(today_prices.values())
        max_idx = [idx for idx, price in today_prices.items() if price == max_price][0]

        now = dt_util.now()
        today_date = now.date()

        hour = max_idx // 4
        minute = (max_idx % 4) * 15
        dt = datetime.combine(today_date, time(hour, minute))
        dt = dt_util.as_local(dt_util.as_utc(dt))

        return {
            "time": dt.isoformat(),
            "interval_index": max_idx,
        }


class SKSpotDailyAverageSensor(CoordinatorEntity, SensorEntity):
    """Sensor zobrazující průměrnou cenu dnes."""

    _attr_name = "SK Spot Daily Average"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_average"
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
        """Průměrná cena dnes."""
        if self.coordinator.data is None:
            return None

        today_prices = self.coordinator.data.get("today_prices", {})
        if not today_prices:
            return None

        avg_price = sum(today_prices.values()) / len(today_prices)

        if self._unit == UNIT_KWH:
            return round(avg_price / 1000, 6)

        return round(avg_price, 2)
