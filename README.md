# Tuya Shadow (Home Assistant Custom Integration)

This integration retrieves *cloud-only* DP properties from Tuya devices that are visible in the Tuya IoT Developer Platform but **not exposed locally** and **not exposed by the official HA Tuya integration**.

It polls the Tuya Cloud on a configurable interval, parses the property list, and publishes each selected DP as a sensor entity.

## Features

- Works with any Tuya WiFi device supported by the Tuya Cloud
- Supports multiple devices, each with multiple DP codes
- Units and scaling factors per DP
- Pure YAML configuration (no config flow yet)
- Uses Home Assistant's `DataUpdateCoordinator` for efficient updates

## Installation

1. Copy the `tuya_shadow` folder into:

```
/config/custom_components/tuya_shadow/
```

on your Home Assisant server.


2. Restart Home Assistant.

3. Add a configuration block to your `configuration.yaml`:

```yaml
sensor:
- platform: tuya_shadow
 client_id: "YOUR_CLIENT_ID"
 client_secret: "YOUR_CLIENT_SECRET"
 region: "eu"
 scan_interval: 30

 devices:
   - id: "DEVICE_ID"
     name: "My Sensor"
     dps:
       - code: "pressure"
         name: "Pressure"
         unit: "hPa"
         factor: 0.1
```

## Notes
You must enable the Tuya Cloud project and link your devices.
The integration uses only the Tuya Cloud REST API.
This is intended for devices where Tuya Local/LAN protocol does not expose all DPs.

To find your CLIENT_ID and CLIENT_SECRET go to your Tuya Platform, select **cloud** on the left. **Open Project** your project. Under the **Authorization** tab, you will find the *Client ID* and the *Client Secret*. Under the **Devices** tab you will find the *Device ID*'s of your devices. 

To find the DPs of a devices, select **Cloud** -> **API Explorer**. Then under **Devices Control** select **Query Properties**. Paste your device_id and submit request. This gives you the codes to use in the configuration file. 


