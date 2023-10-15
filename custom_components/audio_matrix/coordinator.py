from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
import requests
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class AudioMatrixCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Audio Matrix Coordinator",
            update_interval=timedelta(seconds=30),
        )
        self.host = host

    def getOutputs(self) -> any:
        return requests.get(f"{self.host}/outputs", timeout=5)

    def getInputs(self) -> any:
        return requests.get(f"{self.host}/inputs", timeout=5)

    def setSpeakerSource(self, output_id: str, input_id: str) -> None:
        return requests.post(
            f"{self.host}/save",
            json={"data": [{"output_id": output_id, "input_id": input_id}]},
            timeout=5,
        )

    async def _async_update_data(self):
        data = {}
        outputs_response = await self.hass.async_add_executor_job(self.getOutputs)
        outputs_data = outputs_response.json()

        data["outputs"] = {}
        for op in outputs_data:
            data["outputs"][op["zone_number"]] = op

        inputs_response = await self.hass.async_add_executor_job(self.getInputs)
        inputs_data = inputs_response.json()

        data["inputs"] = {}
        for ip in inputs_data:
            data["inputs"][ip["input_number"]] = ip

        return data
