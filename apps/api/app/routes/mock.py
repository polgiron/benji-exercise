"""Mock receivers: stand-ins for a customer's server, to demo and test every delivery path.

Point an endpoint at e.g. http://localhost:8000/mock/flaky?fail=2. Each receiver checks
the signature first, like a real customer would; a real receiver has its secret in its
own config, ours looks it up from the delivery the `webhook-id` names.
"""

import asyncio
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response

from app.clock import utcnow
from app.models import Delivery
from app.signing import InvalidSignature, verify

router = APIRouter(prefix="/mock", tags=["mock receivers"])

# Requests seen per webhook-id, for /mock/flaky.
_seen: Counter[str] = Counter()


async def _verified(request: Request) -> Response | None:
    """None if the signature is valid, else the 401 a real receiver would answer."""
    body = await request.body()  # raw bytes, before any JSON parsing
    msg_id = request.headers.get("webhook-id", "")
    async with request.app.state.db.sessions() as session:
        delivery = await session.get(Delivery, msg_id)
        secret = delivery.endpoint.secret if delivery else None
    if secret is None:
        return Response("unknown webhook-id", status_code=401)
    try:
        verify(
            secret,
            request.headers,
            body,
            tolerance=request.app.state.settings.signature_tolerance_seconds,
            now=utcnow().timestamp(),
        )
    except InvalidSignature as exc:
        return Response(f"invalid signature: {exc}", status_code=401)
    return None


@router.post("/ok")
async def ok(request: Request) -> Response:
    return await _verified(request) or Response("received", status_code=200)


@router.post("/fail")
async def fail(request: Request) -> Response:
    return await _verified(request) or Response("internal error", status_code=500)


@router.post("/reject")
async def reject(request: Request) -> Response:
    return await _verified(request) or Response("bad request", status_code=400)


@router.post("/flaky")
async def flaky(request: Request, fail: Annotated[int, Query(ge=0, le=20)] = 2) -> Response:
    """Fails the first `fail` requests for each message, then succeeds."""
    if rejected := await _verified(request):
        return rejected
    msg_id = request.headers["webhook-id"]
    _seen[msg_id] += 1
    if _seen[msg_id] <= fail:
        return Response(f"flaky failure {_seen[msg_id]}/{fail}", status_code=503)
    return Response("received", status_code=200)


@router.post("/slow")
async def slow(request: Request, seconds: Annotated[float, Query(ge=0, le=60)] = 15) -> Response:
    """Answers after `seconds`; past the 10 s client timeout, the attempt times out."""
    if rejected := await _verified(request):
        return rejected
    await asyncio.sleep(seconds)
    return Response("received, eventually", status_code=200)
