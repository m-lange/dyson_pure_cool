"""Constants for the Dyson Pure Cool integration."""

DOMAIN = "dyson_pure_cool"

ZEROCONF_TYPE = "_dyson_mqtt._tcp.local."

CONF_HOST = "host"
CONF_SERIAL = "serial"
CONF_CREDENTIAL = "credential"
CONF_DEVICE_TYPE = "device_type"


TIMEOUT = 10

SPEED_RANGE = (1,10)

DYSON_CURRENT_STATE = "CURRENT-STATE"
DYSON_STATE_CHANGE = "STATE-CHANGE"
DYSON_ENVIRONMENTAL_CURRENT_SENSOR_DATA = "ENVIRONMENTAL-CURRENT-SENSOR-DATA"

DYSON_AUTO_MODE = "Auto mode"
DYSON_NIGHT_MODE = "Night mode"
DYSON_AUTO_NIGHT_MODE = "Auto + Night mode"

DIRECTION_FORWARD = "forward"
DIRECTION_REVERSE = "reverse"

ATTR_OSCILLATE_LOWER = "oscillate_lower"
ATTR_OSCILLATE_UPPER = "oscillate_upper"
ATTR_SLEEP_TIMER = "sleep_timer"

