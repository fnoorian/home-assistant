"""The tests for the notify.group platform."""
from os import path

from homeassistant import config as hass_config
import homeassistant.components.demo.notify as demo
from homeassistant.components.group import SERVICE_RELOAD
import homeassistant.components.group.notify as group
import homeassistant.components.notify as notify
from homeassistant.setup import async_setup_component

from tests.async_mock import MagicMock, patch


async def test_send_message_with_data(hass):
    """Test sending a message with to a notify group."""
    service1 = demo.DemoNotificationService(hass)
    service2 = demo.DemoNotificationService(hass)

    service1.send_message = MagicMock(autospec=True)
    service2.send_message = MagicMock(autospec=True)

    def mock_get_service(hass, config, discovery_info=None):
        if config["name"] == "demo1":
            return service1
        return service2

    assert await async_setup_component(
        hass,
        "group",
        {},
    )
    await hass.async_block_till_done()

    with patch.object(demo, "get_service", mock_get_service):
        await async_setup_component(
            hass,
            notify.DOMAIN,
            {
                "notify": [
                    {"name": "demo1", "platform": "demo"},
                    {"name": "demo2", "platform": "demo"},
                ]
            },
        )
        await hass.async_block_till_done()

    service = await group.async_get_service(
        hass,
        {
            "services": [
                {"service": "demo1"},
                {
                    "service": "demo2",
                    "data": {
                        "target": "unnamed device",
                        "data": {"test": "message"},
                    },
                },
            ]
        },
    )

    """Test sending a message with to a notify group."""
    await service.async_send_message(
        "Hello", title="Test notification", data={"hello": "world"}
    )

    await hass.async_block_till_done()

    assert service1.send_message.mock_calls[0][1][0] == "Hello"
    assert service1.send_message.mock_calls[0][2] == {
        "title": "Test notification",
        "data": {"hello": "world"},
    }
    assert service2.send_message.mock_calls[0][1][0] == "Hello"
    assert service2.send_message.mock_calls[0][2] == {
        "target": ["unnamed device"],
        "title": "Test notification",
        "data": {"hello": "world", "test": "message"},
    }


async def test_reload_notify(hass):
    """Verify we can reload the notify service."""

    assert await async_setup_component(
        hass,
        "group",
        {},
    )
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        notify.DOMAIN,
        {
            notify.DOMAIN: [
                {"name": "demo1", "platform": "demo"},
                {"name": "demo2", "platform": "demo"},
                {
                    "name": "group_notify",
                    "platform": "group",
                    "services": [{"service": "demo1"}],
                },
            ]
        },
    )
    await hass.async_block_till_done()

    assert hass.services.has_service(notify.DOMAIN, "demo1")
    assert hass.services.has_service(notify.DOMAIN, "demo2")
    assert hass.services.has_service(notify.DOMAIN, "group_notify")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "group/configuration.yaml",
    )
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "group",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert hass.services.has_service(notify.DOMAIN, "demo1")
    assert hass.services.has_service(notify.DOMAIN, "demo2")
    assert not hass.services.has_service(notify.DOMAIN, "group_notify")
    assert hass.services.has_service(notify.DOMAIN, "new_group_notify")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
