"""SK Spot sensor."""
from datetime import datetime, timedelta, time
import logging
import io

from openpyxl import load_workbook
import aiohttp

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_UNIT, UNIT_MWH, UNIT_KWH

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup senzoru."""
    coordinator = SKSpotCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([SKSpotSensor(coordinator, entry)])


class SKSpotCoordinator(DataUpdateCoordinator):
    """Coordinator pro stahování dat."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""
        super().__init__(
            hass,
            _LOGGER,
            name="SK Spot",
            update_interval=SCAN_INTERVAL,
        )
        self._last_download_date = None
        self._today_prices = {}
        self._tomorrow_prices = {}

    async def _async_update_data(self):
        """Stáhni data."""
        now = dt_util.now()
        today = now.date()
        
        # Stáhni pokud je po 13:05 a ještě jsme dnes nestahovali
        should_download = False
        if now.time() >= time(13, 5):
            if self._last_download_date != today:
                should_download = True
        
        # Nebo pokud nemáme žádná data
        if not self._today_prices and not self._tomorrow_prices:
            should_download = True

        if should_download:
            try:
                await self._fetch_prices(today)
                self._last_download_date = today
                _LOGGER.info("Staženo nových cen pro dnes (%d) a zítra (%d)", 
                           len(self._today_prices), len(self._tomorrow_prices))
            except Exception as err:
                _LOGGER.error("Chyba při stahování: %s", err)
                if not self._today_prices and not self._tomorrow_prices:
                    raise UpdateFailed(f"Chyba: {err}") from err
        
        # Určení aktuální ceny podle 15minutového intervalu
        current_hour = now.hour
        current_minute = now.minute
        # Vypočítat index 15minutového intervalu (0-95)
        quarter_index = (current_hour * 4) + (current_minute // 15)
        
        tomorrow = today + timedelta(days=1)
        
        # Pokud je dnes a máme data
        if self._today_prices:
            current_price = self._today_prices.get(quarter_index)
        else:
            current_price = 0
        
        # Pokud nemáme zítřejší data, nastavíme 0
        if not self._tomorrow_prices:
            self._tomorrow_prices = {i: 0 for i in range(96)}
        
        return {
            "current_price": current_price if current_price is not None else 0,
            "today_prices": self._today_prices,
            "tomorrow_prices": self._tomorrow_prices,
            "last_update": now.isoformat(),
        }

    async def _fetch_prices(self, today):
        """Stáhni a parsuj XLSX pro dnes a zítra."""
        tomorrow = today + timedelta(days=1)
        
        # Stáhnout dnešní ceny
        try:
            self._today_prices = await self._fetch_day_prices(today)
        except Exception as err:
            _LOGGER.warning("Nelze stáhnout dnešní ceny: %s", err)
            self._today_prices = {i: 0 for i in range(96)}
        
        # Stáhnout zítřejší ceny
        try:
            self._tomorrow_prices = await self._fetch_day_prices(tomorrow)
        except Exception as err:
            _LOGGER.warning("Nelze stáhnout zítřejší ceny (možná ještě nejsou dostupné): %s", err)
            self._tomorrow_prices = {i: 0 for i in range(96)}

    async def _fetch_day_prices(self, date):
        """Stáhni ceny pro konkrétní den."""
        delivery_date = date.strftime("%Y-%m-%d")
        
        url = (
            f"https://isot.okte.sk/api/v1/dam/report/detailed"
            f"?lang=sk-SK"
            f"&deliverydayfrom={delivery_date}"
            f"&deliverydayto={delivery_date}"
            f"&format=xlsx"
        )
        
        _LOGGER.debug("Stahuji z: %s", url)
        
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise UpdateFailed(f"HTTP {response.status}")
                content = await response.read()
        
        # Parse XLSX
        workbook = load_workbook(filename=io.BytesIO(content), data_only=True)
        sheet = workbook.active
        
        prices = {}
        
        # Sloupec K = 11. sloupec (index 11)
        # Data začínají od řádku 2
        # Máme 96 řádků (24h * 4 čtvrthodiny)
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, min_col=11, max_col=11), start=0):
            cell = row[0]
            if cell.value is not None and row_idx < 96:
                try:
                    price = float(cell.value)
                    prices[row_idx] = round(price, 4)
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            raise UpdateFailed("Žádná data v XLSX")
        
        return prices


class SKSpotSensor(CoordinatorEntity, SensorEntity):
    """SK Spot Price sensor."""

    _attr_name = "SK Spot Price"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SKSpotCoordinator, entry: ConfigEntry) -> None:
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
        
        # Přidat zítřejší ceny - pouze pokud existují a nejsou 0
        for idx in range(96):
            hour = idx // 4
            minute = (idx % 4) * 15
            
            if idx in tomorrow_prices:
                price = tomorrow_prices[idx]
                # Přeskočit pokud je cena 0 (nedostupná data)
                if price == 0:
                    continue
                    
                dt = datetime.combine(tomorrow_date, time(hour, minute))
                dt = dt_util.as_local(dt_util.as_utc(dt))
                iso_time = dt.isoformat()
                
                if self._unit == UNIT_KWH:
                    price = round(price / 1000, 2)
                else:
                    price = round(price, 2)
                    
                all_prices[iso_time] = price
        
        return all_prices
