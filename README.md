# Ostrom Integration for Home Assistant

This integration allows you to monitor your Ostrom electricity prices and fees in Home Assistant.

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/ostrom-hass` directory to your Home Assistant configuration directory:
   ```bash
   # Replace /config with your actual Home Assistant configuration directory
   cp -r custom_components/ostrom-hass /config/custom_components/
   ```

2. Restart Home Assistant
3. Go to Configuration -> Integrations
4. Click the "+ ADD INTEGRATION" button
5. Search for "Ostrom"
6. Enter your credentials:
   - Client ID
   - Client Secret
   - ZIP Code

### Method 2: HACS Installation (Coming Soon)

1. Make sure you have [HACS](https://hacs.xyz) installed
2. Add this repository as a custom repository in HACS:
   - Repository URL: `https://gitea.idowu.net/abi/ostrom-hass`
   - Category: Integration
3. Click Install
4. Restart Home Assistant
5. Add the integration as described in steps 3-6 above

## Available Sensors

The integration provides the following sensors:

- `sensor.electricity_current_price`: Current electricity price (€/kWh)
- `sensor.electricity_next_hour_price`: Next hour's electricity price (€/kWh)
- `sensor.electricity_lowest_price_today`: Today's lowest price (€/kWh)
- `sensor.electricity_highest_price_today`: Today's highest price (€/kWh)
- `sensor.electricity_base_fee`: Monthly base fee (€)
- `sensor.electricity_grid_fee`: Monthly grid fee (€)

All sensors will appear with the friendly names prefixed with "Ostrom Electricity" in your Home Assistant interface.

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements_dev.txt
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```
