from __future__ import annotations

from ..graph.graph import GTFSGraph
from .point_route import PointRoute
from .types import (
    PathResult,
    PointToPointAlgorithm,
    SearchCriterion,
    SearchMode,
    SearchParameters,
    TourResult,
)
from .tour_route import TourRoute


class GTFSSearchRoute:
    def __init__(self, graph: GTFSGraph):
        self.graph = graph
        self.point_route = PointRoute(graph)
        self.tour_route = TourRoute(graph)

    def search(self, params: SearchParameters) -> PathResult | TourResult:
        if params.mode == SearchMode.AB:
            if not params.end_stop_id:
                raise ValueError("Brak przystanku końcowego dla trybu A -> B.")

            algorithm = params.point_algorithm or PointToPointAlgorithm.DIJKSTRA

            if algorithm == PointToPointAlgorithm.ASTAR:
                if params.criterion == SearchCriterion.TIME:
                    return self.point_route.a_star_time(
                        start_stop_id=params.start_stop_id,
                        end_stop_id=params.end_stop_id,
                        target_datetime=params.departure_datetime,
                        max_waiting=params.max_waiting,
                    )
                else:
                    return self.point_route.a_star_transfers(
                        start_stop_id=params.start_stop_id,
                        end_stop_id=params.end_stop_id,
                        target_datetime=params.departure_datetime,
                        max_waiting=params.max_waiting,
                    )
            else:
                return self.point_route.dijkstra_time(
                    start_stop_id=params.start_stop_id,
                    end_stop_id=params.end_stop_id,
                    target_datetime=params.departure_datetime,
                    max_waiting=params.max_waiting,
                )

        elif params.mode == SearchMode.CYCLE:
            if not params.tour_strategy:
                raise ValueError("Brak wybranej strategii optymalizacji dla trybu CYCLE.")

            return self.tour_route.solve(
                start_stop_id=params.start_stop_id,
                visit_stops=params.visit_stops,
                criterion=params.criterion,
                departure_datetime=params.departure_datetime,
                strategy=params.tour_strategy,
                iterations=params.iterations,
                max_waiting=params.max_waiting,
            )

        else:
            raise ValueError(f"Nieznany tryb wyszukiwania: {params.mode}")