from fastapi import APIRouter, Depends

from app.application.services.connector_service import ConnectorService
from app.domain.models.connector import Connector, ConnectorSource
from app.domain.models.user import User
from app.interfaces.dependencies import get_connector_service, get_current_user
from app.interfaces.schemas.base import APIResponse
from app.domain.models.connector_catalog import CatalogConnector
from app.domain.models.mcp_config import MCPTransport
from app.interfaces.schemas.connector import (
    CatalogConnectorItem,
    CatalogHeaderFieldItem,
    ConnectorEnabledRequest,
    ConnectorItem,
    ConnectorWriteRequest,
    CreateMcpFromUrlRequest,
    CreateFromCatalogRequest,
    ImportMcpJsonRequest,
    ListCatalogResponse,
    ListConnectorsResponse,
    dict_to_pairs,
    pairs_to_dict,
)

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _to_item(connector: Connector) -> ConnectorItem:
    return ConnectorItem(
        id=connector.id,
        name=connector.name,
        server_key=connector.server_key,
        note=connector.note,
        icon_url=connector.icon_url,
        catalog_uid=connector.catalog_uid,
        transport=connector.transport,
        enabled=connector.enabled,
        source=connector.source.value,
        readonly=connector.readonly or connector.source == ConnectorSource.FILE,
        command=connector.command,
        args=connector.args,
        env=dict_to_pairs(connector.env),
        url=connector.url,
        headers=dict_to_pairs(connector.headers),
    )


@router.get("", response_model=APIResponse[ListConnectorsResponse])
async def list_connectors(
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ListConnectorsResponse]:
    connectors = await connector_service.list_connectors(current_user.id)
    return APIResponse.success(
        ListConnectorsResponse(connectors=[_to_item(item) for item in connectors])
    )


@router.post("", response_model=APIResponse[ConnectorItem])
async def create_connector(
    request: ConnectorWriteRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.create_connector(
        current_user.id,
        name=request.name,
        transport=request.transport,
        source=ConnectorSource.FORM,
        note=request.note,
        icon_url=request.icon_url,
        command=request.command,
        args=request.args,
        env=pairs_to_dict(request.env),
        url=request.url,
        headers=pairs_to_dict(request.headers),
    )
    return APIResponse.success(_to_item(connector))


@router.post("/import-json", response_model=APIResponse[ConnectorItem])
async def import_mcp_json(
    request: ImportMcpJsonRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.import_json(current_user.id, request.json)
    return APIResponse.success(_to_item(connector))


@router.post("/from-url", response_model=APIResponse[ConnectorItem])
async def create_mcp_from_url(
    request: CreateMcpFromUrlRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.create_from_url(
        current_user.id, request.url, request.name
    )
    return APIResponse.success(_to_item(connector))


def _to_catalog_item(entry: CatalogConnector) -> CatalogConnectorItem:
    return CatalogConnectorItem(
        uid=entry.uid,
        name=entry.name,
        brief=entry.description,
        icon_url=entry.icon,
        icon_url_dark=entry.icon_dark or entry.icon,
        order=entry.order,
        url=entry.url,
        transport=MCPTransport(entry.transport),
        required_headers=[
            CatalogHeaderFieldItem(
                key=field.key,
                label=field.label or field.key,
                placeholder=field.placeholder,
            )
            for field in entry.headers
        ],
    )


@router.get("/catalog", response_model=APIResponse[ListCatalogResponse])
async def list_catalog(
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ListCatalogResponse]:
    return APIResponse.success(
        ListCatalogResponse(
            connectors=[_to_catalog_item(item) for item in connector_service.list_catalog()]
        )
    )


@router.post("/from-catalog", response_model=APIResponse[ConnectorItem])
async def create_mcp_from_catalog(
    request: CreateFromCatalogRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.create_from_catalog(
        current_user.id,
        catalog_uid=request.catalog_uid,
        headers=pairs_to_dict(request.headers),
    )
    return APIResponse.success(_to_item(connector))


@router.patch("/{connector_id}/enabled", response_model=APIResponse[ConnectorItem])
async def set_connector_enabled(
    connector_id: str,
    request: ConnectorEnabledRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.set_enabled(
        current_user.id,
        connector_id,
        request.enabled,
    )
    return APIResponse.success(_to_item(connector))


@router.patch("/{connector_id}", response_model=APIResponse[ConnectorItem])
async def update_connector(
    connector_id: str,
    request: ConnectorWriteRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorItem]:
    connector = await connector_service.update_connector(
        current_user.id,
        connector_id,
        name=request.name,
        transport=request.transport,
        note=request.note,
        icon_url=request.icon_url,
        command=request.command,
        args=request.args,
        env=pairs_to_dict(request.env),
        url=request.url,
        headers=pairs_to_dict(request.headers),
    )
    return APIResponse.success(_to_item(connector))


@router.delete("/{connector_id}", response_model=APIResponse[None])
async def delete_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[None]:
    await connector_service.delete_connector(current_user.id, connector_id)
    return APIResponse.success()
