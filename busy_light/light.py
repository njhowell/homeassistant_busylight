"""Platform for light integration."""
from __future__ import annotations

import logging


from njhowell_busylight import Auth, BusyLightAPI
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ATTR_XY_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_ONOFF,
    COLOR_MODE_RGB,
    SUPPORT_TRANSITION,
    PLATFORM_SCHEMA,
    LightEntity,
)

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
})


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Busy Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]

    session = async_get_clientsession(hass)

    auth = Auth.Auth(session, host)
    api = BusyLightAPI.BusyLightAPI(auth)
    light = api.get_light()

    # Add devices
    async_add_entities([BusyLight(light)])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]

    session = async_get_clientsession(hass)
    auth = Auth.Auth(session, config[CONF_HOST])
    api = BusyLightAPI.BusyLightAPI(auth)
    light = await api.async_get_light()

    # Add devices
    async_add_entities([BusyLight(light)])



class BusyLight(LightEntity):
    """Representation of a Busy Light."""

    def __init__(self, light) -> None:
        """Initialize aBusy Light."""
        self._light = light
        self._name = light.name
        self._state = None
        self._brightness = None
        self._supported_color_modes = set()
        self._supported_color_modes.add(COLOR_MODE_RGB)
        self._rgb_color = [0,0,255]



    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
        }

    @property
    def color_mode(self) -> str:
        """Return the current color mode of the light."""
        
        return COLOR_MODE_RGB

    @property
    def brightness(self) -> int:
        return 100

    @property
    def supported_color_modes(self) -> set | None:
        """Flag supported features."""
        return self._supported_color_modes

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color."""
        
        return self._rgb_color

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self) -> str:
        return "busylight-uniqueid-123"

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        rgb_color = kwargs.get(ATTR_RGB_COLOR)
        if rgb_color is not None:
            self._rgb_color = rgb_color
        
        await self._light.async_switch(self._rgb_color[0], self._rgb_color[1], self._rgb_color[2])
        #await self._light.async_control(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._light.async_control(False)

    async def async_update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        await self._light.async_update()
        self._state = self._light.is_on
        