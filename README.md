# Tuya Shadow (Home Assistant Custom Integration)

This integration retrieves *cloud-only* DP properties from Tuya devices that are visible in the Tuya IoT Developer Platform but **not exposed locally** and **not exposed by the official HA Tuya integration**.

It polls the Tuya Cloud on a configurable interval, parses the property list, and publishes each selected DP as a sensor entity.

## Features

- Works with any Tuya WiFi device supported by the Tuya Cloud
- Supports multiple devices, each with multiple DP codes
- Units and scaling factors per DP
- Pure YAML configuration (no config flow yet)
- Uses Home Assistant's `DataUpdateCoordinator` for efficient updates

## Quick Start

### 1. Install
Copy the `tuya_shadow` directory to `/config/custom_components/` in your Home Assistant instance. You should have a `/config/custom_components/tuya_shadow` folder. 

### 2. Configure
In `configuration.yaml`, add:

```yaml
sensor:
  - platform: tuya_shadow
    client_id: "YOUR_CLIENT_ID"
    client_secret: "YOUR_CLIENT_SECRET"
    region: "eu"     # or us / cn / in
    scan_interval: 30

    devices:
      - id: "DEVICE_ID_1"
        name: "Barometer"
        dps:
          - code: "pressure"
            name: "Pressure"
            unit: "hPa"
            factor: 0.1
          - code: "temp_current"
            name: "Temperature"
            unit: "°C"
            factor: 0.01

      - id: "DEVICE_ID_2"
        name: "Air Quality Sensor"
        dps:
          - code: "pm25_value"
            name: "PM2.5"
            unit: "µg/m³"
            factor: 1
          - code: "co2_value"
            name: "CO2"
            unit: "ppm"
            factor: 1
```

### 3. Restart Home Assistant
After a full restart, your new sensors will appear in the Entities list.
 

## Notes
You must enable the Tuya Cloud project and link your devices.
The integration uses only the Tuya Cloud REST API.
This is intended for devices where Tuya Local/LAN protocol does not expose all DPs.

To find your CLIENT_ID and CLIENT_SECRET go to your Tuya Platform, select **cloud** on the left. **Open Project** your project. Under the **Authorization** tab, you will find the *Client ID* and the *Client Secret*. Under the **Devices** tab you will find the *Device ID*'s of your devices. 

To find the DPs of a devices, select **Cloud** -> **API Explorer**. Then under **Devices Control** select **Query Properties**. Paste your device_id and submit request. This gives you the codes to use in the configuration file. 

## Troubleshooting
“Integration ‘tuya_shadow’ not found” → ensure folder is custom_components/tuya_shadow/ (not nested), manifest includes platforms: ["sensor"], and restart HA.
“sign invalid” error in logs → check client ID/secret, region, and ensure time on HA machine is correct.

## License

This project is released under the MIT License.  
You are free to use, modify, and distribute it, as long as the original copyright notice is included. See the full LICENSE file for details.

