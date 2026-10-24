from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from shapely.geometry import Point

from .edge import RouteEdge
from .types import IdStop

@dataclass(slots=True)
class StopNode:
    stop_id: IdStop
    name: str
    point: Point
    edges: List[RouteEdge] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stop_id or not isinstance(self.stop_id, str):
            raise ValueError(f"stop_id must be a non-empty string, got: {self.stop_id!r}")
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"name must be a non-empty string, got: {self.name!r}")
        if not isinstance(self.point, Point) or self.point.is_empty:
            raise ValueError(f"point must be a non-empty Point, got: {self.point!r}")

    def add_transit_edge(self, edge: RouteEdge) -> None:
        self.edges.append(edge)

    def get_edges_after(self, min_departure_time: int) -> List[RouteEdge]:
        return [e for e in self.edges if e.departure_time >= min_departure_time]

    @property
    def degree(self) -> int:
        return len(self.edges)

    def __repr__(self) -> str:
        return (
            f"StopNode(id={self.stop_id!r}, name={self.name!r}, "
            f"degree={self.degree}, point=({self.point.y:.5f}, {self.point.x:.5f}))"
        )

    def __hash__(self) -> int:
        return hash(self.stop_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StopNode):
            return NotImplemented
        return self.stop_id == other.stop_id