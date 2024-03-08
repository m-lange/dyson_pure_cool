"""Utility functions for the Dyson Pure Cool integration."""

import time


def mqtt_time():
    """Return current time string for mqtt messages."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
