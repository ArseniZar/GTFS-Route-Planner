from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from random import Random
from typing import Deque

from ..graph.graph import GTFSGraph
from ..graph.types import IdStop
from .base_route import BaseRouteFinder
from .point_route import PointRoute
from .types import (
    PathResult,
    SearchCriterion,
    TourOptimizationStrategy,
    TourResult,
)


class TourRoute(BaseRouteFinder):
    def __init__(self, graph: GTFSGraph):
        super().__init__(graph)
        self.point_route = PointRoute(graph)
        self._route_cache: dict = {}

    def solve(
        self,
        start_stop_id: IdStop,
        visit_stops: list[IdStop],
        criterion: SearchCriterion,
        departure_datetime: datetime,
        strategy: TourOptimizationStrategy = TourOptimizationStrategy.BASIC,
        iterations: int = 80,
        max_waiting: int = 3600,
        seed: int = 42,
    ) -> TourResult:
        if isinstance(criterion, str):
            criterion = SearchCriterion(criterion)
        if isinstance(strategy, str):
            strategy = TourOptimizationStrategy(strategy)

        self._route_cache.clear()

        if not visit_stops:
            return self._evaluate_order(
                start_stop_id=str(start_stop_id),
                visit_order=[],
                criterion=criterion,
                departure_datetime=departure_datetime,
                max_waiting=max_waiting,
            )

        current_order = [str(s) for s in visit_stops]
        current_result = self._evaluate_order(
            start_stop_id=str(start_stop_id),
            visit_order=current_order,
            criterion=criterion,
            departure_datetime=departure_datetime,
            max_waiting=max_waiting,
        )
        best_result = current_result
        best_order = current_order.copy()

        rng = Random(seed)
        n = len(current_order)
        variable_tenure = max(3, n // 2 + 1)
        aspiration_enabled = strategy in {
            TourOptimizationStrategy.ASPIRATION_CRITERION,
            TourOptimizationStrategy.ADAPTIVE,
        }
        sampling_enabled = strategy == TourOptimizationStrategy.ADAPTIVE

        infinite_moves: set[tuple[int, int]] = set()
        history_queue: Deque[tuple[int, int]] = deque(maxlen=variable_tenure)
        history_set: set[tuple[int, int]] = set()

        for _ in range(iterations):
            moves: list[tuple[int, int]] = []
            for i in range(n - 1):
                for j in range(i + 1, n):
                    moves.append((i, j))

            if sampling_enabled and len(moves) > 8:
                sample_size = max(8, len(moves) // 3)
                moves = rng.sample(moves, sample_size)

            best_candidate_result: TourResult | None = None
            best_candidate_order: list[str] | None = None
            best_candidate_move: tuple[int, int] | None = None

            for move in moves:
                i, j = move
                candidate_order = current_order.copy()
                candidate_order[i], candidate_order[j] = candidate_order[j], candidate_order[i]
                move_key = (min(i, j), max(i, j))

                is_restricted = (
                    move_key in infinite_moves
                    if strategy == TourOptimizationStrategy.BASIC
                    else move_key in history_set
                )

                try:
                    candidate_result = self._evaluate_order(
                        start_stop_id=str(start_stop_id),
                        visit_order=candidate_order,
                        criterion=criterion,
                        departure_datetime=departure_datetime,
                        max_waiting=max_waiting,
                    )
                except RuntimeError:
                    continue

                if is_restricted and not (
                    aspiration_enabled
                    and candidate_result.minimized_value < best_result.minimized_value
                ):
                    continue

                if (
                    best_candidate_result is None
                    or candidate_result.minimized_value < best_candidate_result.minimized_value
                ):
                    best_candidate_result = candidate_result
                    best_candidate_order = candidate_order
                    best_candidate_move = move_key

            if best_candidate_result is not None and best_candidate_order is not None:
                current_order = best_candidate_order
                current_result = best_candidate_result

                if current_result.minimized_value < best_result.minimized_value:
                    best_result = current_result
                    best_order = current_order.copy()

                if best_candidate_move is not None:
                    if strategy == TourOptimizationStrategy.BASIC:
                        infinite_moves.add(best_candidate_move)
                    else:
                        history_queue.append(best_candidate_move)
                        history_set.clear()
                        history_set.update(history_queue)

        return self._evaluate_order(
            start_stop_id=str(start_stop_id),
            visit_order=best_order,
            criterion=criterion,
            departure_datetime=departure_datetime,
            max_waiting=max_waiting,
        )

    def _evaluate_order(
        self,
        start_stop_id: str,
        visit_order: list[str],
        criterion: SearchCriterion,
        departure_datetime: datetime,
        max_waiting: int,
    ) -> TourResult:
        current_stop = str(start_stop_id)
        current_datetime = departure_datetime
        legs: list[PathResult] = []
        total_time = 0
        total_transfers = 0
        full_order = [str(start_stop_id), *visit_order, str(start_stop_id)]

        for next_stop in full_order[1:]:
            leg = self._find_route_leg(
                start_stop_id=current_stop,
                end_stop_id=next_stop,
                current_datetime=current_datetime,
                criterion=criterion,
                max_waiting=max_waiting,
            )
            legs.append(leg)
            total_time += leg.total_time
            total_transfers += leg.transfers
            current_datetime = current_datetime + timedelta(seconds=leg.total_time)
            current_stop = next_stop

        minimized_value = total_time if criterion == SearchCriterion.TIME else total_transfers
        return TourResult(
            order=full_order,
            legs=legs,
            minimized_value=minimized_value,
            total_time=total_time,
            total_transfers=total_transfers,
        )

    def _find_route_leg(
        self,
        start_stop_id: str,
        end_stop_id: str,
        current_datetime: datetime,
        criterion: SearchCriterion,
        max_waiting: int,
    ) -> PathResult:
        cache_key = (start_stop_id, end_stop_id, criterion)

        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        if criterion == SearchCriterion.TIME:
            leg = self.point_route.dijkstra_time(
                start_stop_id=start_stop_id,
                end_stop_id=end_stop_id,
                target_datetime=current_datetime,
                max_waiting=max_waiting,
            )
        elif criterion == SearchCriterion.TRANSFERS:
            leg = self.point_route.a_star_transfers(
                start_stop_id=start_stop_id,
                end_stop_id=end_stop_id,
                target_datetime=current_datetime,
                max_waiting=max_waiting,
            )
        else:
            raise ValueError(f"Nieznane kryterium: {criterion}")

        if leg is None:
            raise RuntimeError(f"Brak sciezki: {start_stop_id} -> {end_stop_id}")

        self._route_cache[cache_key] = leg
        return leg