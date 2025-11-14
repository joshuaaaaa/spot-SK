"""SK Spot binary sensors."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup binary sensorů."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SKSpotTomorrowDataSensor(coordinator, entry),
        SKSpotCheapest4BlockSensor(coordinator, entry),
        SKSpotCheapest8BlockSensor(coordinator, entry),
        SKSpotCheapest4BlockTomorrowSensor(coordinator, entry),
        SKSpotCheapest8BlockTomorrowSensor(coordinator, entry),
    ])


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


def find_cheapest_block(prices_dict, block_size):
    """
    Najdi nejlevnější souvislý blok dané velikosti.

    Args:
        prices_dict: Slovník {index: cena}
        block_size: Velikost bloku (počet 15min intervalů)

    Returns:
        tuple: (start_index, end_index, avg_price) nebo None
    """
    if not prices_dict or len(prices_dict) < block_size:
        return None

    # Seřaď indexy
    sorted_indices = sorted(prices_dict.keys())

    # Najdi všechny možné souvislé bloky
    best_block = None
    best_sum = float('inf')

    for i in range(len(sorted_indices) - block_size + 1):
        # Zkontroluj, zda je blok souvislý (indexy jdou po sobě)
        is_continuous = True
        for j in range(block_size - 1):
            if sorted_indices[i + j + 1] != sorted_indices[i + j] + 1:
                is_continuous = False
                break

        if not is_continuous:
            continue

        # Vypočítej celkovou cenu bloku
        block_sum = sum(prices_dict[sorted_indices[i + j]] for j in range(block_size))

        if block_sum < best_sum:
            best_sum = block_sum
            start_idx = sorted_indices[i]
            end_idx = sorted_indices[i + block_size - 1]
            best_block = (start_idx, end_idx, best_sum / block_size)

    return best_block


class SKSpotCheapest4BlockSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor pro indikaci nejlevnějšího bloku 4 intervalů (1 hodina)."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_name = "SK Spot Cheapest 4 Block"
        self._attr_unique_id = f"{entry.entry_id}_cheapest_4_block"

    @property
    def is_on(self) -> bool:
        """Vrať True pokud jsme v nejlevnějším 4-intervalovém bloku."""
        if self.coordinator.data is None:
            return False

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        # Slouč dnešní a zítřejší ceny do jednoho slovníku
        all_prices = today_prices.copy()
        if tomorrow_available:
            # Přidej zítřejší ceny s offsetem 96
            for idx, price in tomorrow_prices.items():
                all_prices[idx + 96] = price

        if not all_prices:
            return False

        # Najdi nejlevnější blok 4 intervalů
        cheapest = find_cheapest_block(all_prices, 4)
        if not cheapest:
            return False

        start_idx, end_idx, _ = cheapest

        # Zjisti aktuální index
        now = dt_util.now()
        current_hour = now.hour
        current_minute = now.minute
        current_idx = (current_hour * 4) + (current_minute // 15)

        # Pokud jsme zítra (po půlnoci a máme zítřejší data)
        today = now.date()
        if self.coordinator._last_download_date and self.coordinator._last_download_date < today:
            # Jsme v novém dni, ale data se ještě neposunula
            current_idx += 96

        # Zkontroluj, zda jsme v bloku
        return start_idx <= current_idx <= end_idx

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        all_prices = today_prices.copy()
        if tomorrow_available:
            for idx, price in tomorrow_prices.items():
                all_prices[idx + 96] = price

        cheapest = find_cheapest_block(all_prices, 4)
        if not cheapest:
            return {}

        start_idx, end_idx, avg_price = cheapest

        # Převeď indexy na časy
        now = dt_util.now()
        today = now.date()

        # Start čas
        if start_idx < 96:
            start_day = today
            start_hour = start_idx // 4
            start_minute = (start_idx % 4) * 15
        else:
            start_day = today + timedelta(days=1)
            actual_idx = start_idx - 96
            start_hour = actual_idx // 4
            start_minute = (actual_idx % 4) * 15

        start_time = datetime.combine(start_day, datetime.min.time().replace(hour=start_hour, minute=start_minute))
        start_time = dt_util.as_local(dt_util.as_utc(start_time))

        # End čas
        if end_idx < 96:
            end_day = today
            end_hour = end_idx // 4
            end_minute = (end_idx % 4) * 15
        else:
            end_day = today + timedelta(days=1)
            actual_idx = end_idx - 96
            end_hour = actual_idx // 4
            end_minute = (actual_idx % 4) * 15

        # Přičti 15 minut k end času (konec intervalu)
        end_time = datetime.combine(end_day, datetime.min.time().replace(hour=end_hour, minute=end_minute))
        end_time = dt_util.as_local(dt_util.as_utc(end_time)) + timedelta(minutes=15)

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "average_price": round(avg_price, 4),
            "duration_minutes": 60,
        }

    @property
    def icon(self):
        """Ikona."""
        if self.is_on:
            return "mdi:lightning-bolt"
        return "mdi:lightning-bolt-outline"


class SKSpotCheapest8BlockSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor pro indikaci nejlevnějšího bloku 8 intervalů (2 hodiny)."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_name = "SK Spot Cheapest 8 Block"
        self._attr_unique_id = f"{entry.entry_id}_cheapest_8_block"

    @property
    def is_on(self) -> bool:
        """Vrať True pokud jsme v nejlevnějším 8-intervalovém bloku."""
        if self.coordinator.data is None:
            return False

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        all_prices = today_prices.copy()
        if tomorrow_available:
            for idx, price in tomorrow_prices.items():
                all_prices[idx + 96] = price

        if not all_prices:
            return False

        cheapest = find_cheapest_block(all_prices, 8)
        if not cheapest:
            return False

        start_idx, end_idx, _ = cheapest

        now = dt_util.now()
        current_hour = now.hour
        current_minute = now.minute
        current_idx = (current_hour * 4) + (current_minute // 15)

        today = now.date()
        if self.coordinator._last_download_date and self.coordinator._last_download_date < today:
            current_idx += 96

        return start_idx <= current_idx <= end_idx

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        today_prices = self.coordinator.data.get("today_prices", {})
        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        all_prices = today_prices.copy()
        if tomorrow_available:
            for idx, price in tomorrow_prices.items():
                all_prices[idx + 96] = price

        cheapest = find_cheapest_block(all_prices, 8)
        if not cheapest:
            return {}

        start_idx, end_idx, avg_price = cheapest

        now = dt_util.now()
        today = now.date()

        if start_idx < 96:
            start_day = today
            start_hour = start_idx // 4
            start_minute = (start_idx % 4) * 15
        else:
            start_day = today + timedelta(days=1)
            actual_idx = start_idx - 96
            start_hour = actual_idx // 4
            start_minute = (actual_idx % 4) * 15

        start_time = datetime.combine(start_day, datetime.min.time().replace(hour=start_hour, minute=start_minute))
        start_time = dt_util.as_local(dt_util.as_utc(start_time))

        if end_idx < 96:
            end_day = today
            end_hour = end_idx // 4
            end_minute = (end_idx % 4) * 15
        else:
            end_day = today + timedelta(days=1)
            actual_idx = end_idx - 96
            end_hour = actual_idx // 4
            end_minute = (actual_idx % 4) * 15

        end_time = datetime.combine(end_day, datetime.min.time().replace(hour=end_hour, minute=end_minute))
        end_time = dt_util.as_local(dt_util.as_utc(end_time)) + timedelta(minutes=15)

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "average_price": round(avg_price, 4),
            "duration_minutes": 120,
        }

    @property
    def icon(self):
        """Ikona."""
        if self.is_on:
            return "mdi:lightning-bolt"
        return "mdi:lightning-bolt-outline"


class SKSpotCheapest4BlockTomorrowSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor pro indikaci nejlevnějšího bloku 4 intervalů (1 hodina) pouze pro zítřek."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_name = "SK Spot Cheapest 4 Block Tomorrow"
        self._attr_unique_id = f"{entry.entry_id}_cheapest_4_block_tomorrow"

    @property
    def is_on(self) -> bool:
        """Vrať True pokud jsme v nejlevnějším 4-intervalovém bloku zítřka."""
        if self.coordinator.data is None:
            return False

        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        if not tomorrow_available or not tomorrow_prices:
            return False

        # Najdi nejlevnější blok 4 intervalů pouze v zítřejších datech
        cheapest = find_cheapest_block(tomorrow_prices, 4)
        if not cheapest:
            return False

        start_idx, end_idx, _ = cheapest

        # Zjisti aktuální index
        now = dt_util.now()
        current_hour = now.hour
        current_minute = now.minute
        current_idx = (current_hour * 4) + (current_minute // 15)

        # Pokud jsme dnes, nejsme v zítřejším bloku
        today = now.date()
        if self.coordinator._last_download_date and self.coordinator._last_download_date >= today:
            return False

        # Jsme v novém dni (po půlnoci), ale data se ještě neposunula
        # Zítřejší data jsou teď vlastně dnešní
        return start_idx <= current_idx <= end_idx

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        if not tomorrow_available or not tomorrow_prices:
            return {}

        cheapest = find_cheapest_block(tomorrow_prices, 4)
        if not cheapest:
            return {}

        start_idx, end_idx, avg_price = cheapest

        # Převeď indexy na časy (zítřejší den)
        now = dt_util.now()
        tomorrow_date = now.date() + timedelta(days=1)

        start_hour = start_idx // 4
        start_minute = (start_idx % 4) * 15
        end_hour = end_idx // 4
        end_minute = (end_idx % 4) * 15

        start_time = datetime.combine(tomorrow_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
        start_time = dt_util.as_local(dt_util.as_utc(start_time))

        end_time = datetime.combine(tomorrow_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
        end_time = dt_util.as_local(dt_util.as_utc(end_time)) + timedelta(minutes=15)

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "average_price": round(avg_price, 4),
            "duration_minutes": 60,
        }

    @property
    def icon(self):
        """Ikona."""
        if self.is_on:
            return "mdi:calendar-arrow-right"
        return "mdi:calendar-outline"


class SKSpotCheapest8BlockTomorrowSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor pro indikaci nejlevnějšího bloku 8 intervalů (2 hodiny) pouze pro zítřek."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Init."""
        super().__init__(coordinator)
        self._attr_name = "SK Spot Cheapest 8 Block Tomorrow"
        self._attr_unique_id = f"{entry.entry_id}_cheapest_8_block_tomorrow"

    @property
    def is_on(self) -> bool:
        """Vrať True pokud jsme v nejlevnějším 8-intervalovém bloku zítřka."""
        if self.coordinator.data is None:
            return False

        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        if not tomorrow_available or not tomorrow_prices:
            return False

        cheapest = find_cheapest_block(tomorrow_prices, 8)
        if not cheapest:
            return False

        start_idx, end_idx, _ = cheapest

        now = dt_util.now()
        current_hour = now.hour
        current_minute = now.minute
        current_idx = (current_hour * 4) + (current_minute // 15)

        today = now.date()
        if self.coordinator._last_download_date and self.coordinator._last_download_date >= today:
            return False

        return start_idx <= current_idx <= end_idx

    @property
    def extra_state_attributes(self):
        """Atributy."""
        if self.coordinator.data is None:
            return {}

        tomorrow_prices = self.coordinator.data.get("tomorrow_prices", {})
        tomorrow_available = self.coordinator.data.get("tomorrow_available", False)

        if not tomorrow_available or not tomorrow_prices:
            return {}

        cheapest = find_cheapest_block(tomorrow_prices, 8)
        if not cheapest:
            return {}

        start_idx, end_idx, avg_price = cheapest

        now = dt_util.now()
        tomorrow_date = now.date() + timedelta(days=1)

        start_hour = start_idx // 4
        start_minute = (start_idx % 4) * 15
        end_hour = end_idx // 4
        end_minute = (end_idx % 4) * 15

        start_time = datetime.combine(tomorrow_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
        start_time = dt_util.as_local(dt_util.as_utc(start_time))

        end_time = datetime.combine(tomorrow_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
        end_time = dt_util.as_local(dt_util.as_utc(end_time)) + timedelta(minutes=15)

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "average_price": round(avg_price, 4),
            "duration_minutes": 120,
        }

    @property
    def icon(self):
        """Ikona."""
        if self.is_on:
            return "mdi:calendar-arrow-right"
        return "mdi:calendar-outline"
