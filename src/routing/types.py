from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List

from ..graph.edge import RouteEdge


class SearchMode(Enum):
    AB = "ab"
    CYCLE = "cycle"

    def __str__(self) -> str:
        return self.value


class PointToPointAlgorithm(Enum):
    DIJKSTRA = "dijkstra"
    ASTAR = "astar"

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            PointToPointAlgorithm.DIJKSTRA: "Algorytm Dijkstry (najkrótsza/najszybsza ścieżka)",
            PointToPointAlgorithm.ASTAR: "Algorytm A* (z heurystyką geograficzną)",
        }
        return descriptions.get(self, "Nieznany")


class TourOptimizationStrategy(Enum):
    BASIC = "basic"
    VARIABLE_TENURE = "variable_tenure"
    ASPIRATION_CRITERION = "aspiration"
    ADAPTIVE = "adaptive"

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            TourOptimizationStrategy.BASIC: "Podstawowa strategia przeszukiwania (nieskończona lista)",
            TourOptimizationStrategy.VARIABLE_TENURE: "Ze zmiennym rozmiarem bufora historii",
            TourOptimizationStrategy.ASPIRATION_CRITERION: "Z kryterium aspiracji",
            TourOptimizationStrategy.ADAPTIVE: "Adaptacyjna strategia (z próbkowaniem sąsiadów)",
        }
        return descriptions.get(self, "Nieznany")


class SearchCriterion(Enum):
    TIME = "t"
    TRANSFERS = "p"

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            SearchCriterion.TIME: "Minimalizacja czasu podróży",
            SearchCriterion.TRANSFERS: "Minimalizacja przesiadek",
        }
        return descriptions.get(self, "Nieznany")


@dataclass(frozen=True)
class SearchParameters:
    mode: SearchMode
    start_stop_id: str
    criterion: SearchCriterion
    departure_datetime: datetime
    end_stop_id: str | None = None
    visit_stops: list[str] = field(default_factory=list)
    point_algorithm: PointToPointAlgorithm | None = None
    tour_strategy: TourOptimizationStrategy | None = None
    iterations: int = 80
    max_waiting: int = 3600


@dataclass
class PathResult:
    path_edges: List[RouteEdge]
    total_time: int
    total_distance: float
    transfers: int
    start_stop_id: str
    end_stop_id: str


@dataclass
class TourResult:
    order: list[str]
    legs: list[PathResult]
    minimized_value: int
    total_time: int
    total_transfers: int