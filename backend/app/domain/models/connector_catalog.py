from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CatalogHeaderField(BaseModel):
    """A header the operator marked as required before install."""

    key: str
    label: str = ""
    placeholder: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class CatalogConnector(BaseModel):
    """One Apps entry from the operator-edited connectors.json."""

    uid: str
    name: str
    description: str = ""
    icon: Optional[str] = None
    icon_dark: Optional[str] = Field(default=None, validation_alias="iconDark")
    order: int = 0
    url: str
    transport: str
    headers: List[CatalogHeaderField] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
