from __future__ import annotations

from typing import Dict, List
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import AudioMatrixCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    outputs = coordinator.data["outputs"]
    outputs = dict(filter(lambda x: x[1]["name"] is not None, outputs.items()))
    async_add_entities(
        [AudioMatrixMediaPlayer(coordinator, k, v["name"]) for k, v in outputs.items()]
    )


class Input:
    def __init__(self, input_number: str, name: str) -> None:
        self.input_number = input_number
        self.name = name


class InputProvider:
    def __init__(self, data: dict[int, dict[str, str | int]]) -> None:
        self.inputs: list[Input] = []
        self.inputMapping = {}
        self.inputNameMapping = {}

        for _id, d in data.items():
            ip = Input(d["input_number"], d["name"])
            self.inputs.append(ip)
            self.inputMapping[ip.input_number] = ip
            self.inputNameMapping[ip.name] = ip

    def getInput(self, input_number: str) -> Input:
        return self.inputMapping[input_number]

    def getInputFromName(self, name: str) -> Input:
        return self.inputNameMapping[name]

    def getAvailableInputNames(self) -> list[str]:
        names = [ip.name for ip in self.inputs]
        return list(filter(lambda n: len(n) > 0, names))


class AudioMatrixMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    _attr_name = None
    _attr_assumed_state = True

    _attr_supported_features = MediaPlayerEntityFeature.SELECT_SOURCE

    def __init__(
        self, coordinator: AudioMatrixCoordinator, zone_number, zone_name
    ) -> None:
        super().__init__(coordinator, context=zone_number)
        self._attr_unique_id = f"{zone_name}-{zone_number}-mediaplayer"
        self._attr_name = f"{zone_name} Speaker"
        self._attr_state = MediaPlayerState.ON
        self._sources = []
        self._mediasource = ""
        self._zone_number = zone_number
        self._zone_name = zone_name
        self.input_provider = None
        self._setSourcesFromCoordinator()

    def _setSourcesFromCoordinator(self):
        data = self.coordinator.data
        output = data["outputs"][self._zone_number]
        self.input_provider = InputProvider(data["inputs"])
        self._mediasource = self.input_provider.getInput(output["input_number"]).name
        self._sources = self.input_provider.getAvailableInputNames()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._setSourcesFromCoordinator()
        self.async_write_ha_state()

    @property
    def source_list(self) -> list[str] | None:
        """Return the list of available input sources."""
        return sorted(self._sources)

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        return self._mediasource

    async def async_select_source(self, source: str) -> None:
        self._mediasource = source
        await self.hass.async_add_executor_job(
            self.coordinator.setSpeakerSource,
            self._zone_number,
            self.input_provider.getInputFromName(source).input_number,
        )
        await self.coordinator.async_request_refresh()
