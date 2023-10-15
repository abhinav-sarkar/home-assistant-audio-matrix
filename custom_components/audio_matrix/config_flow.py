"""Config flow for Audio Matrix."""
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector
import ipaddress

import voluptuous as vol

from .const import DOMAIN, LOGGER


class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        _errors = {}
        if user_input is not None:
            try:
                self._ip_v4_validator(user_input[CONF_HOST])
            except vol.Invalid as exception:
                LOGGER.exception(exception)
                _errors["base"] = "address"
            else:
                return self.async_create_entry(
                    title="Audio Matrix",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "host",
                        default=(user_input or {}).get(CONF_HOST),
                        description="Audio Matrix IP Address",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        "port",
                        default=(user_input or {}).get(CONF_PORT, "80"),
                        description="Audio Matrix Port",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.NUMBER
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    def _ip_v4_validator(self, value: str) -> str:
        """Validate that value is parsable as IPv4 address."""
        try:
            address = ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError as ex:
            raise vol.Invalid(
                f"value '{value}' is not a valid IPv4 address: {ex}"
            ) from ex
        return str(address)
