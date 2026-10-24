from __future__ import annotations

from datetime import datetime
import heapq
from typing import Dict, List

from ..graph.edge import RouteEdge
from ..graph.graph import GTFSGraph
from ..graph.node import StopNode
from ..graph.types import IdStop
from .base_route import BaseRouteFinder
from .types import PathResult


class PointRoute(BaseRouteFinder):
    def __init__(self, graph: GTFSGraph):
        super().__init__(graph)

    def dijkstra_time(
        self,
        start_stop_id: IdStop,
        end_stop_id: IdStop,
        target_datetime: datetime,
        max_waiting: int = 3600,
    ) -> PathResult:
        target_date = target_datetime.date()
        departure_time = int(
            target_datetime.hour * 3600
            + target_datetime.minute * 60
            + target_datetime.second
        )

        active_services = self.graph.get_services_for_date(target_date)
        if not active_services:
            raise ValueError(f"Brak aktywnych usług dla daty: {target_date}")

        filtered_nodes = self.graph.get_filtered_nodes_for_date(target_date)
        start_node = filtered_nodes.get(str(start_stop_id))
        end_node = filtered_nodes.get(str(end_stop_id))
        if start_node is None or end_node is None:
            raise ValueError(
                f"Nie znaleziono przystanku: {start_stop_id} lub {end_stop_id}"
            )

        g_score: Dict[StopNode, int] = {start_node: departure_time}
        came_from: Dict[StopNode, tuple[StopNode, RouteEdge]] = {}

        open_heap: list[tuple[int, int, StopNode]] = []
        closed_nodes: set[StopNode] = set()
        counter = 0
        heapq.heappush(open_heap, (departure_time, counter, start_node))

        while open_heap:
            curr_time, _, curr_node = heapq.heappop(open_heap)

            if curr_node in closed_nodes:
                continue

            if curr_node == end_node:
                return self._reconstruct_path(
                    came_from, end_node, start_node, departure_time, curr_time
                )

            closed_nodes.add(curr_node)

            for edge in curr_node.edges:
                wait = edge.departure_time - curr_time
                if curr_node != start_node and wait > max_waiting:
                    continue
                if wait < -30:
                    continue

                next_node = edge.target
                tentative_g = edge.arrival_time

                if tentative_g < g_score.get(next_node, float("inf")):
                    came_from[next_node] = (curr_node, edge)
                    g_score[next_node] = tentative_g
                    if next_node in closed_nodes:
                        closed_nodes.remove(next_node)
                    counter += 1
                    heapq.heappush(open_heap, (tentative_g, counter, next_node))

        raise RuntimeError(f"Path not found: {start_stop_id} -> {end_stop_id}")

    def a_star_time(
        self,
        start_stop_id: IdStop,
        end_stop_id: IdStop,
        target_datetime: datetime,
        max_waiting: int = 3600,
    ) -> PathResult:
        target_date = target_datetime.date()
        departure_time = int(
            target_datetime.hour * 3600
            + target_datetime.minute * 60
            + target_datetime.second
        )

        active_services = self.graph.get_services_for_date(target_date)
        if not active_services:
            raise ValueError(f"Brak aktywnych usług dla daty: {target_date}")

        filtered_nodes = self.graph.get_filtered_nodes_for_date(target_date)
        start_node = filtered_nodes.get(str(start_stop_id))
        end_node = filtered_nodes.get(str(end_stop_id))
        if start_node is None or end_node is None:
            raise ValueError(
                f"Nie znaleziono przystanku: {start_stop_id} lub {end_stop_id}"
            )

        def heuristic(node: StopNode) -> float:
            return self._haversine_m(
                node.point.y, node.point.x, end_node.point.y, end_node.point.x
            ) / 33.3

        g_score: Dict[StopNode, int] = {start_node: departure_time}
        came_from: Dict[StopNode, tuple[StopNode, RouteEdge]] = {}
        open_heap: list[tuple[float, int, int, StopNode]] = []
        closed_nodes: set[StopNode] = set()
        counter = 0

        heapq.heappush(
            open_heap,
            (
                departure_time + heuristic(start_node),
                departure_time,
                counter,
                start_node,
            ),
        )

        while open_heap:
            _, curr_time, _, curr_node = heapq.heappop(open_heap)

            if curr_node in closed_nodes:
                continue

            if curr_node == end_node:
                return self._reconstruct_path(
                    came_from, end_node, start_node, departure_time, curr_time
                )

            closed_nodes.add(curr_node)

            for edge in curr_node.edges:
                wait = edge.departure_time - curr_time
                if curr_node != start_node and wait > max_waiting:
                    continue
                if wait < -30:
                    continue

                next_node = edge.target
                tentative_g = edge.arrival_time

                if tentative_g < g_score.get(next_node, float("inf")):
                    came_from[next_node] = (curr_node, edge)
                    g_score[next_node] = tentative_g
                    if next_node in closed_nodes:
                        closed_nodes.remove(next_node)
                    counter += 1
                    heapq.heappush(
                        open_heap,
                        (tentative_g + heuristic(next_node), tentative_g, counter, next_node),
                    )

        raise RuntimeError(f"Path not found: {start_stop_id} -> {end_stop_id}")

    def a_star_transfers(
        self,
        start_stop_id: IdStop,
        end_stop_id: IdStop,
        target_datetime: datetime,
        max_waiting: int = 3600,
    ) -> PathResult:
        target_date = target_datetime.date()
        departure_time = int(
            target_datetime.hour * 3600
            + target_datetime.minute * 60
            + target_datetime.second
        )

        active_services = self.graph.get_services_for_date(target_date)
        if not active_services:
            raise ValueError(f"Brak aktywnych usług dla daty: {target_date}")

        filtered_nodes = self.graph.get_filtered_nodes_for_date(target_date)
        start_node = filtered_nodes.get(str(start_stop_id))
        end_node = filtered_nodes.get(str(end_stop_id))
        if start_node is None or end_node is None:
            raise ValueError(
                f"Nie znaleziono przystanku: {start_stop_id} lub {end_stop_id}"
            )

        def heuristic(node: StopNode) -> float:
            if node == end_node:
                return 0.0
            return self._haversine_m(
                node.point.y, node.point.x, end_node.point.y, end_node.point.x
            ) / 33.3

        start_state = (start_node, None)
        g_score: Dict[tuple[StopNode, str | None], tuple[int, int]] = {
            start_state: (0, departure_time)
        }
        came_from: Dict[
            tuple[StopNode, str | None],
            tuple[tuple[StopNode, str | None], RouteEdge],
        ] = {}

        open_heap: list[tuple[int, int, float, int, StopNode, str | None]] = []
        counter = 0
        heapq.heappush(
            open_heap,
            (
                0,
                departure_time,
                departure_time + heuristic(start_node),
                counter,
                start_node,
                None,
            ),
        )

        best_goal_state: tuple[StopNode, str | None] | None = None

        while open_heap:
            transfers, curr_time, _, _, curr_node, curr_route = heapq.heappop(open_heap)
            state = (curr_node, curr_route)

            best_for_state = g_score.get(state)
            if best_for_state is None or best_for_state != (transfers, curr_time):
                continue

            if curr_node == end_node:
                best_goal_state = state
                break

            for edge in curr_node.edges:
                wait = edge.departure_time - curr_time
                if curr_node != start_node and wait > max_waiting:
                    continue
                if wait < -30:
                    continue

                next_node = edge.target
                next_route = edge.route_name
                next_time = edge.arrival_time
                transfer_inc = 0 if curr_route is None or curr_route == next_route else 1

                next_state = (next_node, next_route)
                new_cost = (transfers + transfer_inc, next_time)
                old_cost = g_score.get(next_state)

                if old_cost is None or new_cost < old_cost:
                    g_score[next_state] = new_cost
                    came_from[next_state] = (state, edge)
                    counter += 1
                    heapq.heappush(
                        open_heap,
                        (
                            new_cost[0],
                            new_cost[1],
                            new_cost[1] + heuristic(next_node),
                            counter,
                            next_node,
                            next_route,
                        ),
                    )

        if best_goal_state is None:
            raise RuntimeError(f"Path not found: {start_stop_id} -> {end_stop_id}")

        path_edges: List[RouteEdge] = []
        current_state = best_goal_state
        while current_state in came_from:
            prev_state, edge = came_from[current_state]
            path_edges.append(edge)
            current_state = prev_state

        path_edges.reverse()

        if start_node != end_node and not path_edges:
            raise RuntimeError("Path reconstruction failed: empty edge list")

        final_arrival = g_score[best_goal_state][1]
        total_time = int(final_arrival - departure_time)
        total_dist = sum(e.distance_m for e in path_edges)
        final_transfers = g_score[best_goal_state][0]

        return PathResult(
            path_edges=path_edges,
            total_time=total_time,
            total_distance=total_dist,
            transfers=final_transfers,
            start_stop_id=start_node.stop_id,
            end_stop_id=end_node.stop_id,
        )

    def _reconstruct_path(
        self,
        came_from: Dict[StopNode, tuple[StopNode, RouteEdge]],
        end_node: StopNode,
        start_node: StopNode,
        departure_time: int,
        arrival_time: int,
    ) -> PathResult:
        path_edges: List[RouteEdge] = []
        current_node = end_node
        while current_node in came_from:
            from_node, edge = came_from[current_node]
            path_edges.append(edge)
            current_node = from_node

        path_edges.reverse()

        if start_node != end_node and not path_edges:
            raise RuntimeError("Path reconstruction failed: empty edge list")

        total_time = int(arrival_time - departure_time)
        total_dist = sum(e.distance_m for e in path_edges)
        transfers = 0

        for i in range(1, len(path_edges)):
            if path_edges[i].route_name != path_edges[i - 1].route_name:
                transfers += 1

        return PathResult(
            path_edges=path_edges,
            total_time=total_time,
            total_distance=total_dist,
            transfers=transfers,
            start_stop_id=start_node.stop_id,
            end_stop_id=end_node.stop_id,
        )