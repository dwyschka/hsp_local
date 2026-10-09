"""Constants for the Haas+Sohn local integration."""

from typing import Final

DOMAIN: Final = "hsp_local"

CONF_HOST: Final = "host"
CONF_PIN: Final = "pin"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Polling defaults (seconds). The original bridge used 15 seconds.
DEFAULT_SCAN_INTERVAL: Final = 15
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 600

MANUFACTURER: Final = "Haas+Sohn"

# Header value sent along with commands. The official app uses the vendor
# backend URL; the local module only validates that the header is present.
BACKEND_IP: Final = "https://app.haassohn.com"
