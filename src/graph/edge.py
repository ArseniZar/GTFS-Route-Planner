from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import StopNode


@dataclass(slots=True, frozen=True)
class RouteEdge:
    target: StopNode
    departure_time: int     
    arrival_time: int       
    route_name: str        
    service_id: str
    trip_id: str
    distance_m: float        

    def __post_init__(self) -> None:
        if self.target is None:
            raise ValueError("target (StopNode) cannot be None")
        
        if not isinstance(self.departure_time, int):
            raise ValueError(f"departure_time must be int, got: {type(self.departure_time).__name__}")
        if self.departure_time < 0:
            raise ValueError(f"departure_time cannot be negative, got: {self.departure_time}")
        
        if not isinstance(self.arrival_time, int):
            raise ValueError(f"arrival_time must be int, got: {type(self.arrival_time).__name__}")
        if self.arrival_time < 0:
            raise ValueError(f"arrival_time cannot be negative, got: {self.arrival_time}")
        if self.arrival_time < self.departure_time:
            raise ValueError(f"arrival_time ({self.arrival_time}) cannot be before departure_time ({self.departure_time})")
        
        if not self.route_name or not isinstance(self.route_name, str):
            raise ValueError(f"route_name must be a non-empty string, got: {self.route_name!r}")
        
        if not self.service_id or not isinstance(self.service_id, str):
            raise ValueError(f"service_id must be a non-empty string, got: {self.service_id!r}")
        
        if not self.trip_id or not isinstance(self.trip_id, str):
            raise ValueError(f"trip_id must be a non-empty string, got: {self.trip_id!r}")
        
        if not isinstance(self.distance_m, (int, float)):
            raise ValueError(f"distance_m must be number, got: {type(self.distance_m).__name__}")
        if self.distance_m < 0:
            raise ValueError(f"distance_m cannot be negative, got: {self.distance_m}")


    @property
    def travel_time(self) -> int:
        return self.arrival_time - self.departure_time

    @staticmethod
    def format_hms(seconds: int) -> str:
        hh = seconds // 3600
        mm = (seconds % 3600) // 60
        ss = seconds % 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    @property
    def departure_time_hms(self) -> str:
        return self.format_hms(self.departure_time)

    @property
    def arrival_time_hms(self) -> str:
        return self.format_hms(self.arrival_time)

    def __repr__(self) -> str:
        dep_h = self.departure_time // 3600
        dep_m = (self.departure_time % 3600) // 60
        arr_h = self.arrival_time // 3600
        arr_m = (self.arrival_time % 3600) // 60
        return (f"Edge(to={self.target.stop_id}, line={self.route_name}, "
                f"dep={dep_h:02d}:{dep_m:02d}, arr={arr_h:02d}:{arr_m:02d})")