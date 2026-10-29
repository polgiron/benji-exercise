from fastapi import APIRouter

from app.deps import Session
from app.schemas import EndpointCreate, EndpointCreated, EndpointOut, EndpointUpdate
from app.services import endpoints as service

router = APIRouter(prefix="/api/endpoints", tags=["endpoints"])


@router.get("")
async def list_endpoints(session: Session) -> list[EndpointOut]:
    return [EndpointOut.model_validate(e) for e in await service.list_endpoints(session)]


@router.post("", status_code=201)
async def create_endpoint(data: EndpointCreate, session: Session) -> EndpointCreated:
    return EndpointCreated.model_validate(await service.create_endpoint(session, data))


@router.get("/{endpoint_id}")
async def get_endpoint(endpoint_id: str, session: Session) -> EndpointOut:
    return EndpointOut.model_validate(await service.get_endpoint(session, endpoint_id))


@router.patch("/{endpoint_id}")
async def update_endpoint(endpoint_id: str, data: EndpointUpdate, session: Session) -> EndpointOut:
    endpoint = await service.update_endpoint(session, endpoint_id, data)
    return EndpointOut.model_validate(endpoint)
