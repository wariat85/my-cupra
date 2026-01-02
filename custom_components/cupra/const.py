"""Constants for the CUPRA integration."""

from datetime import timedelta

DOMAIN = "cupra"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_REGION = "eu"
MANUFACTURER = "CUPRA"

REGIONS = ["eu", "na", "apac"]

CONF_REGION = "region"
CONF_VIN = "vin"
CONF_VEHICLE_NAME = "vehicle_name"
CONF_VEHICLE_MODEL = "vehicle_model"

STORAGE_KEY = f"{DOMAIN}_credentials"
STORAGE_VERSION = 1
