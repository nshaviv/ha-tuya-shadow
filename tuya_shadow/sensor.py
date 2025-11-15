import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .api import TuyaShadowApi
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REGION,
    CONF_DEVICES,
    CONF_DPS,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up Tuya Shadow sensors from YAML."""

    client_id = config[CONF_CLIENT_ID]
    client_secret = config[CONF_CLIENT_SECRET]
    region = config.get(CONF_REGION, "eu")
    scan_interval = config.get("scan_interval", DEFAULT_UPDATE_INTERVAL)

    # Cast to int for safety
    try:
        scan_interval = int(scan_interval)
    except Exception:
        _LOGGER.warning(
            "Invalid scan_interval=%s, using default %s",
            scan_interval,
            DEFAULT_UPDATE_INTERVAL,
        )
        scan_interval = DEFAULT_UPDATE_INTERVAL

    devices_cfg = config[CONF_DEVICES]

    api = TuyaShadowApi(client_id, client_secret, region)

    # Build internal mapping
    devices = {}
    for dev in devices_cfg:
        dev_id = dev["id"]
        dev_name = dev.get(CONF_NAME, dev_id)
        dps_list = dev[CONF_DPS]

        parsed_dps = []
        for dp in dps_list:
            parsed_dps.append(
                {
                    "code": dp["code"],
                    "name": dp.get("name", dp["code"]),
                    "unit": dp.get("unit", None),
                    "factor": dp.get("factor", 1.0),
                }
            )
        devices[dev_id] = {"name": dev_name, "dps": parsed_dps}

    coordinator = TuyaShadowCoordinator(
        hass, api, devices, timedelta(seconds=scan_interval)
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for dev_id, dev_info in devices.items():
        dev_name = dev_info["name"]
        for dp in dev_info["dps"]:
            entities.append(
                TuyaShadowSensor(
                    coordinator=coordinator,
                    device_id=dev_id,
                    device_name=dev_name,
                    dp_code=dp["code"],
                    dp_name=dp["name"],
                    unit=dp["unit"],
                    factor=dp["factor"],
                )
            )

    async_add_entities(entities)


class TuyaShadowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: TuyaShadowApi, devices: dict, interval: timedelta):
        super().__init__(
            hass,
            _LOGGER,
            name="Tuya Shadow Coordinator",
            update_interval=interval,
        )
        self._api = api
        self._devices = devices
        self.data = {}

    async def _async_update_data(self):
        def _fetch():
            out = {}
            for dev_id in self._devices.keys():
                try:
                    props = self._api.get_shadow(dev_id)
                    out[dev_id] = {p["code"]: p["value"] for p in props}
                except Exception as e:
                    _LOGGER.error("Error updating device %s: %s", dev_id, e)
            return out

        new_data = await self.hass.async_add_executor_job(_fetch)
        self.data = new_data
        return new_data


class TuyaShadowSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: TuyaShadowCoordinator,
        device_id: str,
        device_name: str,
        dp_code: str,
        dp_name: str,
        unit: str | None,
        factor: float,
    ):
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._dp_code = dp_code
        self._dp_name = dp_name
        self._unit = unit
        self._factor = factor

        self._attr_name = f"{device_name} {dp_name}"
        self._attr_unique_id = f"tuya_shadow_{device_id}_{dp_code}"

        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        dev_data = self.coordinator.data.get(self._device_id, {})
        raw = dev_data.get(self._dp_code)
        if raw is None:
            return None

        try:
            return raw * self._factor
        except Exception:
            return raw
