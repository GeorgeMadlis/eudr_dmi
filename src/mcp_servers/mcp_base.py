# geodmi_mcp/mcp_base.py

from __future__ import annotations
from typing import Callable, Dict, Any, List, Coroutine, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .models import DatasetRecord, DatasetVersion, BoundingBox, TimeRange, DataPointer


@dataclass
class MCPToolSpec:
    name: str
    description: str
    input_model: Any         # Pydantic model type or dict schema
    output_model: Any        # Pydantic model type or dict schema
    func: Callable[..., Coroutine[Any, Any, Any]]


class MCPServerBase(ABC):
    """
    Base class for all MCP servers. One instance per logical group
    (e.g. GBIF MCP, EO/Climate GEE MCP, Maaamet MCP, OWID MCP).
    """
    id: str                  # unique id, e.g. "gbif_mcp"
    title: str               # human-readable
    dataset_families: List[str] = field(default_factory=list)

    def __init__(self):
        self._tools: Dict[str, MCPToolSpec] = {}

    # --- Tool registration helper -------------------------------------------

    def tool(self, name: str, description: str, input_model: Any, output_model: Any):
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
            self._tools[name] = MCPToolSpec(
                name=name,
                description=description,
                input_model=input_model,
                output_model=output_model,
                func=func,
            )
            return func
        return decorator

    def list_tools(self) -> List[MCPToolSpec]:
        return list(self._tools.values())

    # --- Required common tools ----------------------------------------------

    @abstractmethod
    async def list_datasets(self) -> List[DatasetRecord]:
        """
        Return the subset of Task-1 catalogue this server actually wraps.
        """

    @abstractmethod
    async def get_dataset_metadata(self, dataset_id: str) -> DatasetRecord:
        """
        Enriched metadata for one dataset.
        """

    @abstractmethod
    async def list_updates_since(
        self, since: Optional[TimeRange] = None
    ) -> List[DatasetVersion]:
        """
        Return all observed updates / versions since the given time range boundary.
        """
