# spot-SK


# SK Spot Price - Home Assistant Integration

Integrace pro Home Assistant zobrazující aktuální spotové ceny elektřiny ze slovenského trhu (OKTE).

## Funkce

- Automatické stahování cen každý den v 13:05
- 15minutové intervaly (96 hodnot denně)
- Aktuální cena se mění každých 15 minut (00, 15, 30, 45)
- Zobrazení cen pro dnes a zítra (pokud jsou dostupné)
- Volba jednotek: EUR/MWh nebo EUR/kWh
- Atributy s časovými razítky pro snadné použití v automatizacích

## Instalace

1. Zkopírujte složku `sk_spot` do `<config>/custom_components/`
2. Restartujte Home Assistant
3. Přidejte integraci: Nastavení → Zařízení a služby → Přidat integraci → "SK Spot Price"
4. Vyberte jednotky (EUR/MWh nebo EUR/kWh)

## Zdroj dat

Data jsou stahována z OKTE (Operátor krátkodobého trhu s elektrinou):
https://www.okte.sk/sk/kratkodoby-trh/zverejnenie-udajov-dt/

## Použití v automatizacích
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
buymeacoffee.com/jakubhruby


<img width="300" height="300" alt="qr-code" src="https://github.com/user-attachments/assets/2581bf36-7f7d-4745-b792-d1abaca6e57d" />
