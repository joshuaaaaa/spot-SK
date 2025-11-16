# SK Spot Price - Home Assistant Integration

Integrace pro Home Assistant zobrazující aktuální spotové ceny elektřiny ze slovenského trhu (OKTE).

## Funkce

- **Inteligentní schedulování**: Automatické stahování dat ve 13:05, opakování každých 5 minut pokud zítřejší data ještě nejsou dostupná
- **15minutové intervaly**: 96 hodnot denně (00:00-23:45)
- **Aktuální cena**: Mění se každých 15 minut (00, 15, 30, 45)
- **Data pro dnes a zítra**: Pokud jsou zítřejší ceny dostupné (obvykle od 13:00-14:00)
- **Volba jednotek**: EUR/MWh nebo EUR/kWh
- **Atributy s časovými razítky**: Pro snadné použití v automatizacích

### Sensory pro spotové ceny
- 💰 **Current Price**: Aktuální spotová cena
- 📊 **Current Rank**: Ranking aktuálního bloku (1-96, kde 1=nejlevnější, 96=nejdražší)
- 📉 **Daily Min/Max/Average**: Statistiky dnešních cen

### Binary sensory pro automatizace
- 📅 **Tomorrow Data**: Indikace dostupnosti zítřejších dat
- ⚡ **Cheapest Blocks**: Nejlevnější souvislé bloky 1h/2h (dnes+zítra)
- 📅⚡ **Cheapest Blocks Tomorrow**: Nejlevnější bloky pouze ze zítřka
- 💎 **Top 5/10 Expensive**: Pro automatizaci prodeje elektřiny
- 🔥 **Bottom 5/10 Cheap**: Pro automatizaci spotřeby v nejlevnějších blocích

## Sensory

Po instalaci budete mít k dispozici:

### Hlavní sensory
- `sensor.sk_spot_price` - Aktuální spotová cena
  - Stav: Cena v EUR/MWh nebo EUR/kWh (podle nastavení)
  - Atributy: Všechny ceny pro dnes + zítra (až 192 záznamů)

### Ranking sensory
- `sensor.sk_spot_current_rank` - Ranking aktuálního 15min bloku
  - Stav: Číslo 1-96 (1 = nejlevnější, 96 = nejdražší)
  - Atributy: `today_rankings`, `tomorrow_rankings` (mapování časů na ranky)
  - **Použití**: Umožňuje jednoduché automatizace typu "prodávej el. při ranku >= 92" (top 5 nejdražších bloků)
  - **Poznámka**: Bloky se stejnou cenou mají stejný rank (standard ranking)

### Statistické sensory
- `sensor.sk_spot_daily_min` - Minimální cena dnes
  - Atributy: `time` (kdy nastane), `interval_index`

- `sensor.sk_spot_daily_max` - Maximální cena dnes
  - Atributy: `time` (kdy nastane), `interval_index`

- `sensor.sk_spot_daily_average` - Průměrná cena dnes

### Binary Sensory
- `binary_sensor.sk_spot_tomorrow_data` - Dostupnost zítřejších dat
  - ON: Zítřejší data jsou k dispozici
  - OFF: Zítřejší data ještě nejsou dostupná
  - Atributy: `tomorrow_records_count`, `expected_records`, `data_complete`

- `binary_sensor.sk_spot_cheapest_4_block` - Nejlevnější 1 hodina
  - ON: Právě probíhá nejlevnější souvislý blok 4 intervalů (1 hodina)
  - Atributy: `start_time`, `end_time`, `average_price`, `duration_minutes`

- `binary_sensor.sk_spot_cheapest_8_block` - Nejlevnějších 2 hodiny
  - ON: Právě probíhá nejlevnější souvislý blok 8 intervalů (2 hodiny)
  - Atributy: `start_time`, `end_time`, `average_price`, `duration_minutes`

- `binary_sensor.sk_spot_cheapest_4_block_tomorrow` - Nejlevnější 1 hodina zítřka
  - ON: Právě probíhá nejlevnější souvislý blok 4 intervalů (1 hodina) pouze ze zítřejších dat
  - OFF: Pokud zítřejší data nejsou dostupná nebo nejsme v bloku
  - Atributy: `start_time`, `end_time`, `average_price`, `duration_minutes`

- `binary_sensor.sk_spot_cheapest_8_block_tomorrow` - Nejlevnějších 2 hodiny zítřka
  - ON: Právě probíhá nejlevnější souvislý blok 8 intervalů (2 hodiny) pouze ze zítřejších dat
  - OFF: Pokud zítřejší data nejsou dostupná nebo nejsme v bloku
  - Atributy: `start_time`, `end_time`, `average_price`, `duration_minutes`

### Ranking Binary Sensory
- `binary_sensor.sk_spot_in_top_5_expensive` - Top 5 nejdražších bloků
  - ON: Jsme v top 5 nejdražších 15min blocích dnes
  - Atributy: `current_rank`, `total_blocks`, `threshold_rank`
  - **Použití**: Spustit prodej elektřiny do sítě

- `binary_sensor.sk_spot_in_top_10_expensive` - Top 10 nejdražších bloků
  - ON: Jsme v top 10 nejdražších 15min blocích dnes
  - Atributy: `current_rank`, `total_blocks`, `threshold_rank`

- `binary_sensor.sk_spot_in_bottom_5_cheap` - Bottom 5 nejlevnějších bloků
  - ON: Jsme v bottom 5 nejlevnějších 15min blocích dnes
  - Atributy: `current_rank`, `total_blocks`, `threshold_rank`
  - **Použití**: Spustit spotřebiče, nabíjet baterii

- `binary_sensor.sk_spot_in_bottom_10_cheap` - Bottom 10 nejlevnějších bloků
  - ON: Jsme v bottom 10 nejlevnějších 15min blocích dnes
  - Atributy: `current_rank`, `total_blocks`, `threshold_rank`

## Instalace (HACS)

1. Přidej tento repozitář do HACS jako vlastní repozitář.
2. Nainstaluj **SK Spot Price** integraci.
3. Restartuj Home Assistant.
4. Přidej integraci přes **Nastavení → Zařízení a služby → Přidat integraci → SK Spot**.


## Instalace manuální

1. Zkopírujte složku `sk_spot` do `<config>/custom_components/`
2. Restartujte Home Assistant
3. Přidejte integraci: Nastavení → Zařízení a služby → Přidat integraci → "SK Spot Price"
4. Vyberte jednotky (EUR/MWh nebo EUR/kWh)

## Zdroj dat

Data jsou stahována z OKTE (Operátor krátkodobého trhu s elektrinou):
https://www.okte.sk/sk/kratkodoby-trh/zverejnenie-udajov-dt/

## Použití v automatizacích

### Základní příklad - nízká cena
```yaml
automation:
  - alias: "Zapni spotřebič při nízké ceně"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sk_spot_price
        below: 0.05
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.bojler
```

### Nejlevnější 1 hodina - nabíjení baterie
```yaml
automation:
  - alias: "Nabít baterii v nejlevnější hodině"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_cheapest_4_block
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.battery_charger
      - service: notify.mobile_app
        data:
          message: >
            Začíná nejlevnější hodina!
            Průměrná cena: {{ state_attr('binary_sensor.sk_spot_cheapest_4_block', 'average_price') }} EUR/MWh
            Do: {{ state_attr('binary_sensor.sk_spot_cheapest_4_block', 'end_time') }}

  - alias: "Zastavit nabíjení po nejlevnější hodině"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_cheapest_4_block
        to: "off"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.battery_charger
```

### Nejlevnějších 2 hodiny - bojler
```yaml
automation:
  - alias: "Zapnout bojler v nejlevnějších 2 hodinách"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_cheapest_8_block
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.water_heater

  - alias: "Vypnout bojler po nejlevnějším období"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_cheapest_8_block
        to: "off"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.water_heater
```

### Notifikace - upozornění před levným obdobím
```yaml
automation:
  - alias: "Upozornění 15 minut před nejlevnější hodinou"
    trigger:
      - platform: time_pattern
        minutes: "/15"
    condition:
      - condition: template
        value_template: >
          {% set start = state_attr('binary_sensor.sk_spot_cheapest_4_block', 'start_time') | as_datetime %}
          {% set now = now() %}
          {{ (start - now).total_seconds() > 0 and (start - now).total_seconds() <= 900 }}
    action:
      - service: notify.mobile_app
        data:
          message: >
            Za 15 minut začíná nejlevnější hodina!
            Čas: {{ state_attr('binary_sensor.sk_spot_cheapest_4_block', 'start_time') }}
            Průměr: {{ state_attr('binary_sensor.sk_spot_cheapest_4_block', 'average_price') }} EUR/MWh
```

### Notifikace - dostupnost zítřejších dat
```yaml
automation:
  - alias: "Upozornění na dostupnost zítřejších dat"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_tomorrow_data
        from: "off"
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Zítřejší spotové ceny jsou dostupné!
            Počet záznamů: {{ state_attr('binary_sensor.sk_spot_tomorrow_data', 'tomorrow_records_count') }}/96
```

### Plánování na zítřek - nejlevnější hodina zítřka
```yaml
automation:
  - alias: "Informace o nejlevnější hodině zítřka"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_tomorrow_data
        from: "off"
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Zítřejší nejlevnější hodina:
            {{ state_attr('binary_sensor.sk_spot_cheapest_4_block_tomorrow', 'start_time') | as_datetime | as_local }}
            Průměrná cena: {{ state_attr('binary_sensor.sk_spot_cheapest_4_block_tomorrow', 'average_price') }} EUR/MWh
```

### Automatické spuštění v nejlevnější hodině zítřka
```yaml
automation:
  - alias: "Spustit úlohu v nejlevnější hodině zítřka"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_cheapest_4_block_tomorrow
        to: "on"
    condition:
      # Ověř, že je to opravdu zítra (po půlnoci)
      - condition: template
        value_template: >
          {{ now().hour < 13 }}
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.scheduled_task
```

### Prodej elektřiny v top 5 nejdražších blocích (pomocí rankingu)
```yaml
automation:
  - alias: "Prodávat elektřinu v top 5 nejdražších blocích"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_in_top_5_expensive
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.battery_discharge_to_grid
      - service: notify.mobile_app
        data:
          message: >
            Prodej elektřiny zahájen!
            Aktuální rank: {{ state_attr('binary_sensor.sk_spot_in_top_5_expensive', 'current_rank') }}/96
            Cena: {{ states('sensor.sk_spot_price') }} EUR/MWh

  - alias: "Zastavit prodej po top 5 blocích"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_in_top_5_expensive
        to: "off"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.battery_discharge_to_grid
```

### Spotřeba v bottom 10 nejlevnějších blocích
```yaml
automation:
  - alias: "Zapnout bojler v bottom 10 nejlevnějších blocích"
    trigger:
      - platform: state
        entity_id: binary_sensor.sk_spot_in_bottom_10_cheap
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.water_heater
```

### Automatizace založená na ranku (custom threshold)
```yaml
automation:
  - alias: "Prodávat elektřinu při ranku >= 90"
    trigger:
      - platform: state
        entity_id: sensor.sk_spot_current_rank
    condition:
      - condition: numeric_state
        entity_id: sensor.sk_spot_current_rank
        above: 89
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.sell_to_grid

  - alias: "Zastavit prodej při ranku < 90"
    trigger:
      - platform: state
        entity_id: sensor.sk_spot_current_rank
    condition:
      - condition: numeric_state
        entity_id: sensor.sk_spot_current_rank
        below: 90
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.sell_to_grid
```

## Výhody rankingového systému

Nový rankingový systém přináší mnoho výhod pro surfování na spotovém trhu:

### 1. Jednoduché automatizace pro prodej elektřiny
Místo složitých výpočtů stačí nastavit: "Prodávej při ranku >= 92" = top 5 nejdražších bloků
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.sk_spot_current_rank
    above: 91  # Top 5 nejdražších
```

### 2. Flexibilní prahy
- Top 5: rank >= 92
- Top 10: rank >= 87
- Top 20: rank >= 77
- Bottom 5: rank <= 5
- Bottom 10: rank <= 10

### 3. Kombinace s dalšími podmínkami
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.sk_spot_current_rank
    above: 91
  - condition: state
    entity_id: sensor.battery_level
    above: 80
```

### 4. Přehledné atributy
Sensor `sk_spot_current_rank` obsahuje atributy:
- `today_rankings`: Slovník všech dnešních ranků (čas → rank)
- `tomorrow_rankings`: Slovník všech zítřejších ranků (pokud dostupné)

Umožňuje plánování: "Zítra v 10:00 bude rank 15, ideální pro nabíjení"

### 5. Standard ranking pro stejné ceny
Pokud mají bloky stejnou cenu, mají stejný rank:
- Například: 2 bloky s cenou 100 EUR → oba mají rank 1
- Další blok s cenou 150 EUR → má rank 3 (přeskočí rank 2)
- Výhoda: Pokud je více bloků s nejnižší cenou, všechny budou mít rank 1

## Technické detaily

### Inteligentní schedulování
Integrace používá vlastní schedulování místo fixního update intervalu:

- **Před 13:05**: Naplánuje update na 13:05 (+ 0-120s jitter)
- **Po 13:05 s daty**: Další update zítra ve 13:05
- **Po 13:05 bez zítřejších dat**: Opakuje pokus za 5 minut
- **Výhody**: Minimální zátěž API (~2-3 requesty denně místo 1440)

### Automatické obnovení dat
- Po půlnoci se zítřejší data automaticky přesunou na dnešní
- Scheduler automaticky naplánuje stahování nových dat
- Při restartu HA se data stáhnou okamžitě (pokud chybí)

### Přesnost bloků
Binary sensory pro nejlevnější bloky:
- Hledají nejlevnější **souvislé** bloky (musí jít po sobě)
- **Cheapest Block** (bez "Tomorrow"): Prohledává všechna dostupná data (dnes + zítra dohromady)
- **Cheapest Block Tomorrow**: Prohledává **pouze zítřejší data**
- Aktualizují se každých 15 minut společně s cenou
- Průměrná cena bloku se počítá ze všech intervalů v bloku

**Rozdíl mezi standardními a tomorrow bloky:**
- `cheapest_4_block`: Najde nejlevnější 1h z celého období (dnes 00:00 - zítra 23:45)
- `cheapest_4_block_tomorrow`: Najde nejlevnější 1h pouze ze zítřka (zítra 00:00 - 23:45)
- Užitečné pro plánování: "Co budu dělat zítra v nejlevnější hodině?"

## Vizualizace pomocí ApexCharts

Pro zobrazení grafu cen nainstalujte [ApexCharts Card](https://github.com/RomRider/apexcharts-card) a použijte tuto konfiguraci:
```yaml
type: custom:apexcharts-card
graph_span: 48h
span:
  start: day
  offset: +0H
header:
  title: Spotová cena elektřiny
  show: true
  show_states: true
  colorize_states: true
hours_12: false
stacked: false
experimental:
  color_threshold: true
all_series_config:
  show:
    legend_value: false
    datalabels: false
    extremas: true
    in_brush: true
  float_precision: 2
  type: area
  invert: false
  fill_raw: last
  color_threshold:
    - value: -1
      color: 1E90FF
    - value: 2.5
      color: "008000"
    - value: 3.5
      color: DAA520
    - value: 4.5
      color: FF0000
now:
  show: true
  label: Now
  color: red
series:
  - entity: sensor.sk_spot_price
    name: Aktuální hodina
    opacity: 0.7
    extend_to: now
    type: column
    show:
      in_header: raw
    data_generator: |
      return Object.entries(entity.attributes).map(([date, value], index) => {
        return [new Date(date).getTime(), value];
      });
       
apex_config:
  chart:
    height: 400px
    animations:
      enabled: true
      easing: easeinout
      speed: 800
      animateGradually:
        enabled: true
        delay: 150
    zoom:
      enabled: true
      type: x
      autoScaleYaxis: true
      zoomedArea:
        fill:
          color: "#90CAF9"
          opacity: 0.4
        stroke:
          color: "#0D47A1"
          opacity: 0.4
          width: 1
  legend:
    show: false
    floating: true
    offsetY: 25
  yaxis:
    opposite: false
    reversed: false
    logarithmic: false
    decimalsInFloat: 2
    labels:
      show: true
    tooltip:
      enabled: true
    crosshairs:
      show: true
  xaxis:
    labels:
      show: true
      rotate: -45
      rotateAlways: true
    logarithmic: true
  stroke:
    show: true
    curve: stepline
    lineCap: butt
    colors: undefined
  plotOptions:
    candlestick:
      colors:
        upward: "#00B746"
        downward: "#EF403C"
      wick:
        useFillColor: true
  markers:
    size: 0
  grid:
    show: true
    strokeDashArray: 1
    position: front
    xaxis:
      lines:
        show: true
```

---
MIT License © 2025 [@joshuaaaaa](https://github.com/joshuaaaaa)

## Support

If you like this card, please ⭐ star this repository!

Found a bug or have a feature request? Please open an issue.



## http://buymeacoffee.com/jakubhruby


<img width="150" height="150" alt="qr-code" src="https://github.com/user-attachments/assets/2581bf36-7f7d-4745-b792-d1abaca6e57d" />
