from fastapi import APIRouter, Depends

from app.application.services.connector_service import ConnectorService
from app.domain.models.connector import ConnectorCatalogItem, UserConnector
from app.domain.models.user import User
from app.interfaces.dependencies import get_connector_service, get_current_user
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.connector import (
    ConnectBuiltinRequest,
    ConnectedConnectorItem,
    ConnectorCatalogItemResponse,
    ConnectorEnvFieldItem,
    ConnectorsStateResponse,
    CreateCustomConnectorRequest,
    TestConnectorRequest,
    TestConnectorResponse,
    UpdateConnectorRequest,
)

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _to_catalog_item(item: ConnectorCatalogItem) -> ConnectorCatalogItemResponse:
    return ConnectorCatalogItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        category=item.category,
        icon_url=item.icon_url,
        transport=item.transport,
        command=item.command,
        args=item.args,
        url=item.url,
        env_fields=[
            ConnectorEnvFieldItem(
                key=field.key,
                label=field.label,
                secret=field.secret,
                placeholder=field.placeholder,
            )
            for field in item.env_fields
        ],
        header_fields=[
            ConnectorEnvFieldItem(
                key=field.key,
                label=field.label,
                secret=field.secret,
                placeholder=field.placeholder,
            )
            for field in item.header_fields
        ],
    )


def _to_connected_item(connector: UserConnector) -> ConnectedConnectorItem:
    return ConnectedConnectorItem(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        icon_url=connector.icon_url,
        source=connector.source.value,
        catalog_id=connector.catalog_id,
        transport=connector.transport,
        command=connector.command,
        args=connector.args,
        url=connector.url,
        headers=connector.headers,
        env=connector.env,
        enabled=connector.enabled,
    )


def _to_state(catalog, connected) -> ConnectorsStateResponse:
    return ConnectorsStateResponse(
        catalog=[_to_catalog_item(item) for item in catalog],
        connected=[_to_connected_item(item) for item in connected],
    )


@router.get("", response_model=APIResponse[ConnectorsStateResponse])
async def get_connectors_state(
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorsStateResponse]:
    catalog, connected = await connector_service.get_state(current_user.id)
    return APIResponse.success(_to_state(catalog, connected))


@router.post("/builtin", response_model=APIResponse[ConnectorsStateResponse])
async def connect_builtin_connector(
    request: ConnectBuiltinRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorsStateResponse]:
    await connector_service.connect_builtin(
        current_user.id,
        request.catalog_id,
        env=request.env,
        headers=request.headers,
    )
    catalog, connected = await connector_service.get_state(current_user.id)
    return APIResponse.success(_to_state(catalog, connected))


@router.post("/custom", response_model=APIResponse[ConnectorsStateResponse])
async def create_custom_connector(
    request: CreateCustomConnectorRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorsStateResponse]:
    await connector_service.create_custom(
        current_user.id,
        name=request.name,
        description=request.description,
        icon_url=request.icon_url,
        transport=request.transport,
        command=request.command,
        args=request.args,
        url=request.url,
        headers=request.headers,
        env=request.env,
    )
    catalog, connected = await connector_service.get_state(current_user.id)
    return APIResponse.success(_to_state(catalog, connected))


@router.patch("/connected/{connector_id}", response_model=APIResponse[ConnectedConnectorItem])
async def update_connector(
    connector_id: str,
    request: UpdateConnectorRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectedConnectorItem]:
    connector = await connector_service.update_connector(
        current_user.id,
        connector_id,
        enabled=request.enabled,
        name=request.name,
        description=request.description,
        transport=request.transport,
        command=request.command,
        args=request.args,
        url=request.url,
        headers=request.headers,
        env=request.env,
    )
    return APIResponse.success(_to_connected_item(connector))


@router.delete("/connected/{connector_id}", response_model=APIResponse[ConnectorsStateResponse])
async def delete_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[ConnectorsStateResponse]:
    await connector_service.delete_connector(current_user.id, connector_id)
    catalog, connected = await connector_service.get_state(current_user.id)
    return APIResponse.success(_to_state(catalog, connected))


@router.post("/test", response_model=APIResponse[TestConnectorResponse])
async def test_connector(
    request: TestConnectorRequest,
    current_user: User = Depends(get_current_user),
    connector_service: ConnectorService = Depends(get_connector_service),
) -> APIResponse[TestConnectorResponse]:
    success, message, tools = await connector_service.test_connection(
        transport=request.transport,
        command=request.command,
        args=request.args,
        url=request.url,
        headers=request.headers,
        env=request.env,
    )
    return APIResponse.success(
        TestConnectorResponse(success=success, message=message, tools=tools)
    )
