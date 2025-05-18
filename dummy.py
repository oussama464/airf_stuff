# tests/test_card_source.py

import logging
import pytest
import trio

from card import CardSource, MAX_REQUEST_SENT
from card import ImadResponse  # your real response type


class DummyResponse(ImadResponse):
    """
    A minimal stand-in for your real ImadResponse.
    """
    def __init__(self, identifier: str, status_code: int):
        self.identifier = identifier
        self.status_code = status_code

    def __eq__(self, other):
        return (
            isinstance(other, DummyResponse)
            and self.identifier == other.identifier
            and self.status_code == other.status_code
        )


@pytest.fixture
def source_with_missing(monkeypatch):
    # 1) Create an “empty” CardSource and give it a list of identifiers
    source = CardSource.__new__(CardSource)
    source.identifiers = ["b", "a", "c"]

    # 2) Ensure the semaphore limit is high enough
    monkeypatch.setattr("card.MAX_REQUEST_SENT", len(source.identifiers))

    # 3) Prepare fake responses: 'b' → 404, others → 200
    responses = {
        "a": DummyResponse("a", 200),
        "b": DummyResponse("b", 404),
        "c": DummyResponse("c", 200),
    }

    async def fake_send_request(self, identifier):
        # emulate network I/O
        await trio.sleep(0)
        return responses[identifier]

    monkeypatch.setattr(CardSource, "_send_request", fake_send_request)
    return source, list(responses.values())


@pytest.fixture
def source_all_ok(monkeypatch):
    source = CardSource.__new__(CardSource)
    source.identifiers = ["x", "y", "z"]
    monkeypatch.setattr("card.MAX_REQUEST_SENT", len(source.identifiers))

    responses = {
        k: DummyResponse(k, 200) for k in source.identifiers
    }

    async def fake_send_request(self, identifier):
        await trio.sleep(0)
        return responses[identifier]

    monkeypatch.setattr(CardSource, "_send_request", fake_send_request)
    return source, list(responses.values())


@pytest.mark.trio
async def test_send_bulk_request_sorts_and_logs_missing(source_with_missing, caplog):
    source, expected = source_with_missing
    caplog.set_level(logging.INFO)

    results = await source._send_bulk_request()

    # should return them sorted by .identifier
    assert results == sorted(expected, key=lambda r: r.identifier)

    # and log about the single missing identifier "b"
    assert "1 identifiers are not in the CARD database: b" in caplog.text


@pytest.mark.trio
async def test_send_bulk_request_no_log_when_all_present(source_all_ok, caplog):
    source, expected = source_all_ok
    caplog.set_level(logging.INFO)

    results = await source._send_bulk_request()

    assert results == sorted(expected, key=lambda r: r.identifier)
    # no INFO‐level message at all
    assert caplog.text.strip() == ""
