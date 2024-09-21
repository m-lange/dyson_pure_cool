"""Provides functionality to interact Dyson Pure Cool fans."""

from collections.abc import Callable
import json
import logging
import threading

import paho.mqtt.client as mqtt

from .const import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    DYSON_AUTO_MODE,
    DYSON_AUTO_NIGHT_MODE,
    DYSON_CURRENT_STATE,
    DYSON_ENVIRONMENTAL_CURRENT_SENSOR_DATA,
    DYSON_NIGHT_MODE,
    DYSON_STATE_CHANGE,
    TIMEOUT,
)
from .exceptions import DysonCannotConnect, DysonInvalidAuth, DysonNotConnected
from .utils import mqtt_time

_LOGGER = logging.getLogger(__name__)


class DysonPureCool:
    """Provides functionality to control a dyson fan."""

    def __init__(self, serial: str, credential: str,  device_type: str):
        """Initialize dyson fan with serial, credential and device type."""

        self._serial = serial
        self._credential = credential
        self._device_type = device_type

        self._mqttc = mqtt.Client(protocol=mqtt.MQTTv31)
        self._mqttc.username_pw_set(self._serial, self._credential)
        self._mqttc.on_connect = self._on_connect
        self._mqttc.on_disconnect = self._on_disconnect
        self._mqttc.on_message = self._on_message
        self._mqttc.enable_logger(_LOGGER)

        self._status_topic = f"{device_type}/{serial}/status/current"
        self._command_topic = f"{device_type}/{serial}/command"

        self._connected = threading.Event()
        self._disconnected = threading.Event()
        self._state_data_available = threading.Event()
        self._envionment_data_available = threading.Event()
        self._state_data = None
        self._environmental_data = None
        self._error = None
        self._update_listeners = []


    def connect(self, host: str) -> None:
        """Connect the client to a broker."""
        self._host = host

        self._disconnected.clear()

        self._mqttc.connect_async(host)
        self._mqttc.loop_start()

        if self._connected.wait(timeout=TIMEOUT):
            if self._error is not None:
                self._mqttc.disconnect()
                raise self._error

            _LOGGER.debug("Connected to Dyson Pure Cool (%s) %s", self._device_type, self._serial)

            # Request and wait for first data
            if self._request_first_data():
                return

        # Close connection if timeout or connected but failed to get data
        self.disconnect()
        raise DysonNotConnected("Not connected")


    def disconnect(self) -> None:
        """Disconnect from the broker cleanly."""
        self._mqttc.disconnect()


    def _on_connect(self, client, userdata, flags, rc):
        """Called when the broker responds to our connection request."""  # noqa: D401

        self._connected.set()
        self._disconnected.clear()

        if rc == mqtt.CONNACK_REFUSED_PROTOCOL_VERSION:
            self._error = DysonCannotConnect("Connection refused - incorrect protocol version")
        elif rc == mqtt.CONNACK_REFUSED_IDENTIFIER_REJECTED:
            self._error = DysonCannotConnect("Connection refused - invalid client identifier")
        elif rc == mqtt.CONNACK_REFUSED_SERVER_UNAVAILABLE:
            self._error = DysonCannotConnect("Connection refused - server unavailable")
        elif rc == mqtt.CONNACK_REFUSED_BAD_USERNAME_PASSWORD:
            self._error = DysonInvalidAuth("Connection refused - bad username or password")
        elif rc == mqtt.CONNACK_REFUSED_NOT_AUTHORIZED:
            self._error = DysonCannotConnect("Connection refused - not authorised")
        elif rc == mqtt.CONNACK_ACCEPTED:
            self._mqttc.subscribe(self._status_topic)
            self._error = None

        self._mqttc.subscribe(self._status_topic)


    def _on_disconnect(self, client, userdata, rc):
        """Called when the client disconnects from the broker."""  # noqa: D401

        _LOGGER.debug("Disconnected with result code %s", str(rc))
        self._connected.clear()
        self._disconnected.set()


    def _on_message(self, client, userdata, msg):
        """Called when a message has been received on a topic that the client subscribes to."""  # noqa: D401

        payload = json.loads(msg.payload.decode("utf-8"))
        if payload["msg"] in [DYSON_CURRENT_STATE, DYSON_STATE_CHANGE]:
            self._state_data_available.set()
            self._state_data = payload["product-state"]

            if payload["msg"] == DYSON_STATE_CHANGE:
                for func in self._update_listeners:
                    func(self, self._state_data)

        if payload["msg"] == DYSON_ENVIRONMENTAL_CURRENT_SENSOR_DATA:
            self._envionment_data_available.set()
            self._environmental_data = payload["data"]


    def _request_first_data(self) -> bool:
        """Request and wait for first data."""

        self.request_current_state()
        self.request_envionment_data()

        state = self._state_data_available.wait(timeout=TIMEOUT)
        envionment = self._envionment_data_available.wait(timeout=TIMEOUT)

        return state and envionment


    def request_current_state(self) -> None:
        """Request current state from the broker."""
        payload = {
            "msg": "REQUEST-CURRENT-STATE",
            "time": mqtt_time(),
        }

        self._mqttc.publish(self._command_topic, json.dumps(payload))


    def request_envionment_data(self) -> None:
        """Request environment sensor data from the broker."""
        payload = {
            "msg": "REQUEST-PRODUCT-ENVIRONMENT-CURRENT-SENSOR-DATA",
            "time": mqtt_time(),
        }

        self._mqttc.publish(self._command_topic, json.dumps(payload))


    def _set_configuration(self, **kwargs: dict) -> None:
        """Send a state-set message to the broker."""
        payload = json.dumps(
            {
                "msg": "STATE-SET",
                "time": mqtt_time(),
                "mode-reason": "LAPP",
                "data": kwargs,
            }
        )

        self._mqttc.publish(self._command_topic, payload, 1)


    def _get_field_value(self, field: str) -> str:
        """Get value of a field received from the broker in state or environment sensor data."""

        if field in self._state_data:
            if isinstance(self._state_data[field], list):
                return self._state_data[field][1]
            return self._state_data[field]

        if field in self._environmental_data:
            return self._environmental_data[field]

        return None


    def add_update_listener(self, func) -> Callable[[], None] :
        """Add a function to call when state-change mesaage has been received."""

        self._update_listeners.append(func)
        return lambda: self._update_listeners.remove(func)


    @property
    def serial(self) -> str:
        """Return serial number of the device."""
        return self._serial


    @property
    def device_type(self):
        """Return type identification of the device."""
        return self._device_type


    @property
    def current_direction(self) -> str:
        """Set the direction of the fan."""
        if self._get_field_value("fdir") == "ON":
            return DIRECTION_FORWARD
        return DIRECTION_REVERSE


    @property
    def is_on(self) -> bool:
        """Return true if the device is on."""
        return self._get_field_value("fpwr") == "ON"


    @property
    def speed(self) -> int:
        """Set the speed of the fan."""
        fnsp = self._get_field_value("fnsp")
        if fnsp == "AUTO":
            return None
        return int(fnsp)


    @property
    def oscillating(self) -> bool:
        """Return whether or not the fan is currently oscillating."""
        return self._get_field_value("oson") in ["OION", "ON"]


    @property
    def oscillate_lower(self) -> int:
        """Return lower boundary of the oscillation."""
        osal = self._get_field_value("osal")
        return int(osal)


    @property
    def oscillate_upper(self) -> int:
        """Return upper boundary of the oscillation."""
        osau = self._get_field_value("osau")
        return int(osau)


    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        auto = self._get_field_value("auto")
        nmod = self._get_field_value("nmod")

        if auto == "ON" and nmod == "ON":
            return DYSON_AUTO_NIGHT_MODE
        if auto == "ON":
            return DYSON_AUTO_MODE
        if nmod == "ON":
            return DYSON_NIGHT_MODE
        return None


    @property
    def error_code(self) -> str:
        """Return error code of the device."""
        return self._get_field_value("ercd")


    @property
    def warning_code(self) -> str:
        """Return warning code of the device."""
        return self._get_field_value("wacd")


    @property
    def temperature(self) -> int:
        """Indoor temperature.

        Monitor the ambient temperature to help
        maintain a comfortable environment.
        """
        tact = self._get_field_value("tact")
        return round( (float(tact) / 10) - 273.15, 1)


    @property
    def humidity(self) -> int:
        """Indoor humidity.

        The amount of water vapour in the air,
        shown as a percentage.
        """
        hact = self._get_field_value("hact")
        return int(hact)

    @property
    def pm25(self) -> int:
        """Particulate matter (PM2.5).

        Microscopic particles up to 2.5 microns in size,
        suspended in the air we breathe. These include
        smoke, bacteria and allergens.
        """
        pm25 = self._get_field_value("pm25")
        try:
            return int(pm25)
        except ValueError:
            return None

    @property
    def pm10(self) -> int:
        """Particulate matter (PM10).

        Larger microscopic particles up to 10 microns
        in size, suspended in the air we breathe. These
        include dust, mould and pollen.
        """
        pm10 = self._get_field_value("pm10")
        try:
            return int(pm10)
        except ValueError:
            return None

    @property
    def voc(self) -> int:
        """Volatile organic compounds.

        VOCs are typically odours that may be
        potentially harmful. These can be found in
        cleaning products, paints and furnishings.
        """
        va10 = self._get_field_value("va10")
        try:
            return int(va10)
        except ValueError:
            return None

    @property
    def nox(self) -> int:
        """Nitrogen dioxide and other oxidising gases.

        These potentially harmful gases are released
        into the air by combustion, for example, the
        burning gas when cooking and in vehicle
        exhaust emissions.
        """
        noxl = self._get_field_value("noxl")
        try:
            return int(noxl)
        except ValueError:
            return None

    @property
    def carbon_filter_life(self) -> int:
        """Carbon filter life.

        The remaining filter life is shown
        will indicate when your filters need
        replacing
        """
        cflr = self._get_field_value("cflr")
        try:
            return int(cflr)
        except ValueError:
            return None

    @property
    def hepa_filter_life(self) -> int:
        """HEPA filter life.

        The remaining filter life is shown
        will indicate when your filters need
        replacing
        """
        hflr = self._get_field_value("hflr")
        try:
            return int(hflr)
        except ValueError:
            return None

    @property
    def sleep_timer(self) -> int:
        """Remaining time of the sleep timer in minutes; 0 if disabled."""
        sltm = self._get_field_value("sltm")
        return 0 if sltm == "OFF" else int(sltm)

    @property
    def continuous_monitoring(self) -> bool:
        """Continuous monitoring.

        With continuous monitoring turned on, your Dyson fan will gather
        air quality, temperature and humidity information, which is displayed on the
        LCD screen and in the Dyson Link app.
        """
        return self._get_field_value("rhtm") == "ON"


    def set_direction(self, direction: str) -> None:
        """Set the airflow direction of the fan."""
        if direction == DIRECTION_FORWARD:
            self._set_configuration(fdir="ON")
        else:
            self._set_configuration(fdir="OFF")


    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        fpwr = self._get_field_value("fpwr")
        if preset_mode == DYSON_AUTO_NIGHT_MODE:
            self._set_configuration(fpwr = "ON", auto="ON", nmod="ON")
        elif preset_mode == DYSON_AUTO_MODE:
            self._set_configuration(fpwr = "ON", auto="ON",nmod="OFF")
        elif preset_mode == DYSON_NIGHT_MODE:
            self._set_configuration(fpwr = fpwr, auto="OFF", nmod="ON")
        else:
            self._set_configuration(fpwr = fpwr, auto="OFF", nmod="OFF")


    def turn_on(self) -> None:
        """Turn on the fan."""
        self._set_configuration(fpwr = "ON", fnsp=f"{self.speed:04d}")


    def turn_off(self) -> None:
        """Turn off the fan."""
        self._set_configuration(fpwr = "OFF")


    def set_speed(self, speed: int) -> None:
        """Set the speed of the fan."""
        if speed not in range(1, 11):
            raise ValueError(f"Invalid airflow speed {speed}")
        self._set_configuration(fpwr="ON", fnsp=f"{speed:04d}")


    def oscillate(self, oscillating: bool, osal: int | None, osau: int | None) -> None:
        """Oscillate the fan."""
        if oscillating:

            if osal is None:
                osal = self.oscillate_lower
            if osau is None:
                osau = self.oscillate_upper

            if osal > osau:
                osal, osau = osau, osal

            osal = max(osal, 5)
            osau = min(osau, 355)

            if abs(osal - osau) < 30:
                osal = osau = int(osal + abs(osal - osau) / 2)

            oson = "OION" if self._get_field_value("oson") in ["OION", "OIOF"] else "ON"
            self._set_configuration(oson=oson, fpwr="ON", ancp="CUST", osal=f"{osal:04d}", osau=f"{osau:04d}")

        else:
            oson = "OIOF" if self._get_field_value("oson") in ["OION", "OIOF"] else "OFF"
            self._set_configuration(oson=oson)


    def set_sleep_timer(self, sltm: int) -> None:
        """Enable sleep timer; pass 0 to disable."""
        self._set_configuration(sltm=f"{sltm:04d}")


    def set_continuous_monitoring(self, rhtm: bool) -> None:
        """Enable or disable Continuous monitoring."""
        self._set_configuration(
            fpwr="ON" if self.is_on else "OFF",
            rhtm="ON" if rhtm else "OFF"
        )
