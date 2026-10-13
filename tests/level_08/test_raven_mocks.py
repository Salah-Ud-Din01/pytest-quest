import json
from unittest.mock import MagicMock
from urllib.error import URLError

import pytest

from dungeon import raven


def make_fake_urlopen(delivery_id="abc123"):
    """A fake urlopen whose response body is {"delivery_id": ...}."""
    response = MagicMock()
    response.read.return_value = json.dumps({"delivery_id": delivery_id}).encode("utf-8")
    fake_urlopen = MagicMock()
    fake_urlopen.return_value.__enter__.return_value = response
    return fake_urlopen


def test_the_raven_returns_the_delivery_id(monkeypatch):
    monkeypatch.setattr(raven, "urlopen", make_fake_urlopen("abc123"))
    assert raven.send_raven("Ada", "Hello") == "abc123"


def test_the_raven_sends_the_right_request(monkeypatch):
    fake = make_fake_urlopen()
    monkeypatch.setattr(raven, "urlopen", fake)
    raven.send_raven("Ada", "Hello")
    fake.assert_called_once()
    request = fake.call_args.args[0]
    assert request.full_url == raven.RAVEN_API
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {"to": "Ada", "message": "Hello"}
    assert fake.call_args.kwargs["timeout"] == raven.TIMEOUT_SECONDS


def test_the_raven_retries_after_failures(monkeypatch):
    working = make_fake_urlopen("abc123")
    fake = MagicMock(side_effect=[URLError("down"), URLError("down"), working.return_value])
    monkeypatch.setattr(raven, "urlopen", fake)
    assert raven.send_raven("Ada", "Hello") == "abc123"
    assert fake.call_count == 3


@pytest.mark.parametrize("attempts", [1, 2, 5])
def test_the_raven_is_lost_when_every_attempt_fails(monkeypatch, attempts):
    fake = MagicMock(side_effect=URLError("down"))
    monkeypatch.setattr(raven, "urlopen", fake)
    with pytest.raises(raven.RavenLostError):
        raven.send_raven("Ada", "Hello", attempts=attempts)
    assert fake.call_count == attempts