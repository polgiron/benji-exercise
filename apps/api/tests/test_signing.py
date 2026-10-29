import pytest

from app.signing import InvalidSignature, generate_secret, signature_headers, verify

BODY = b'{"id":"evt_1","type":"campaign_updated","data":{"campaign_id":"cmp_7"}}'
NOW = 1_800_000_000


def headers(secret, body=BODY, ts=NOW):
    return signature_headers(secret, "dlv_1", body, ts)


def test_valid_signature_passes():
    secret = generate_secret()
    verify(secret, headers(secret), BODY, now=NOW)


def test_secret_format():
    secret = generate_secret()
    assert secret.startswith("whsec_")
    assert secret != generate_secret()


def test_tampered_body_fails():
    secret = generate_secret()
    with pytest.raises(InvalidSignature):
        verify(secret, headers(secret), BODY.replace(b"cmp_7", b"cmp_8"), now=NOW)


def test_wrong_secret_fails():
    with pytest.raises(InvalidSignature):
        verify(generate_secret(), headers(generate_secret()), BODY, now=NOW)


def test_tampered_message_id_fails():
    secret = generate_secret()
    h = headers(secret) | {"webhook-id": "dlv_2"}
    with pytest.raises(InvalidSignature):
        verify(secret, h, BODY, now=NOW)


@pytest.mark.parametrize("skew", [-301, 301])
def test_stale_or_future_timestamp_fails(skew):
    secret = generate_secret()
    with pytest.raises(InvalidSignature, match="tolerance"):
        verify(secret, headers(secret, ts=NOW + skew), BODY, now=NOW)


def test_timestamp_cannot_be_swapped_for_a_fresh_one():
    # Replaying an old request with a new timestamp breaks the signature.
    secret = generate_secret()
    h = headers(secret, ts=NOW - 3600) | {"webhook-timestamp": str(NOW)}
    with pytest.raises(InvalidSignature, match="no matching"):
        verify(secret, h, BODY, now=NOW)


def test_missing_headers_fail():
    with pytest.raises(InvalidSignature, match="missing"):
        verify(generate_secret(), {}, BODY, now=NOW)


def test_any_of_several_signatures_matches():
    old, new = generate_secret(), generate_secret()
    h = headers(new)
    h["webhook-signature"] = f"{headers(old)['webhook-signature']} {h['webhook-signature']}"
    verify(new, h, BODY, now=NOW)


async def test_outgoing_request_verifies_with_the_secret_from_creation(
    make_endpoint, fire, worker, receiver, clock
):
    secret = (await make_endpoint())["secret"]
    await fire()
    await worker.run_once()

    [request] = receiver.requests
    verify(secret, request.headers, request.content, now=clock.now.timestamp())
    assert request.headers["content-type"] == "application/json"


async def test_retries_keep_the_message_id_and_body_but_sign_a_fresh_timestamp(
    make_endpoint, fire, worker, receiver, clock
):
    secret = (await make_endpoint())["secret"]
    receiver.respond(500, 200)
    await fire()
    await worker.run_once()
    clock.advance(600)  # beyond the 5-minute tolerance of the first signature
    await worker.run_once()

    first, second = receiver.requests
    assert first.headers["webhook-id"] == second.headers["webhook-id"]
    assert first.content == second.content
    assert int(second.headers["webhook-timestamp"]) - int(first.headers["webhook-timestamp"]) == 600
    verify(secret, second.headers, second.content, now=clock.now.timestamp())
