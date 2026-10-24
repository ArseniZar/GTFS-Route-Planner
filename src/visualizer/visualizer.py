from __future__ import annotations

import random
from math import atan2, degrees
from pathlib import Path
import sys
from typing import List

import folium

from ..graph.edge import RouteEdge
from ..graph.graph import GTFSGraph
from ..routing.types import PathResult, TourResult


class GTFSVisualizer:
    def __init__(self, graph: GTFSGraph):
        self.graph = graph

    def plot_stops(
        self,
        output_html: str | Path = "gtfs_stops_map.html",
        max_routes: int = 1500,
        show_direction: bool = True,
    ) -> None:
        m = folium.Map(location=[52.0, 19.0], zoom_start=7, tiles="CartoDB positron")

        for node in self.graph.nodes.values():
            if node.point is None:
                continue
            folium.CircleMarker(
                location=[node.point.y, node.point.x],
                radius=5,
                popup=f"<b>{node.name}</b><br>ID: {node.stop_id}",
                color="#333",
                fill=True,
                fill_color="#fff",
                fill_opacity=1.0,
            ).add_to(m)

        print(
            f"   Drawing up to {max_routes} connections (arrows: {'on' if show_direction else 'off'})..."
        )

        route_colors = {}
        palette = ["#d73027", "#fc8d59", "#4575b4", "#91bfdb", "#1a9850", "#fee090"]

        drawn = 0
        nodes_list = list(self.graph.nodes.values())
        random.shuffle(nodes_list)

        for node in nodes_list:
            if node.point is None:
                continue

            for edge in node.edges:
                if edge.target is None or edge.target.point is None:
                    continue

                route = edge.route_name
                if route not in route_colors:
                    route_colors[route] = palette[len(route_colors) % len(palette)]

                start = [node.point.y, node.point.x]
                end = [edge.target.point.y, edge.target.point.x]

                dep_str = f"{edge.departure_time // 3600:02d}:{(edge.departure_time % 3600) // 60:02d}"
                arr_str = f"{edge.arrival_time // 3600:02d}:{(edge.arrival_time % 3600) // 60:02d}"

                folium.PolyLine(
                    locations=[start, end],
                    color=route_colors[route],
                    weight=5,
                    opacity=0.9,
                    tooltip=f"<b>Линия: {route}</b><br>{dep_str} → {arr_str}",
                ).add_to(m)

                if show_direction:
                    mid_lat = (start[0] + end[0]) / 2
                    mid_lon = (start[1] + end[1]) / 2

                    dx = end[1] - start[1]
                    dy = end[0] - start[0]
                    angle = degrees(atan2(dx, dy)) - 90

                    arrow_html = f"""
                    <div style="font-size:18px; 
                                color:{route_colors[route]}; 
                                transform:rotate({angle}deg); 
                                text-shadow: 0px 0px 3px white;">
                        ➤
                    </div>
                    """

                    folium.Marker(
                        location=[mid_lat, mid_lon],
                        icon=folium.DivIcon(
                            html=arrow_html,
                            icon_size=(20, 20),
                            icon_anchor=(10, 10),
                        ),
                    ).add_to(m)

                drawn += 1
                if drawn >= max_routes:
                    break
            if drawn >= max_routes:
                break

        folium.LayerControl().add_to(m)
        m.save(str(output_html))
        print(f"Map with all stops saved to {output_html}")
        print(f"   Connections drawn: {drawn}")

    def plot_result(
        self,
        result: PathResult | TourResult,
        output_html: str | Path = "found_path_map.html",
    ) -> None:
        """Отрисовывает результат поиска (PathResult или TourResult) на карте."""
        path_edges: list[RouteEdge] = []
        start_node_id: str | None = None

        if isinstance(result, TourResult):
            start_node_id = result.order[0] if result.order else None
            for leg in result.legs:
                path_edges.extend(leg.path_edges)
        elif isinstance(result, PathResult):
            start_node_id = result.start_stop_id
            path_edges = result.path_edges

        if not path_edges:
            print("Path is empty!")
            return

        waypoints: list[tuple[float, float, str]] = []

        if start_node_id and start_node_id in self.graph.nodes:
            start_node = self.graph.nodes[start_node_id]
            if start_node.point is not None:
                waypoints.append((start_node.point.y, start_node.point.x, start_node.name))

        for edge in path_edges:
            if edge.target is not None and edge.target.point is not None:
                waypoints.append((
                    edge.target.point.y,
                    edge.target.point.x,
                    edge.target.name,
                ))

        if len(waypoints) < 2:
            print("Not enough points to draw the path!")
            return

        center_lat, center_lon = waypoints[0][0], waypoints[0][1]
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

        for node in self.graph.nodes.values():
            if node.point is None:
                continue
            folium.CircleMarker(
                location=[node.point.y, node.point.x],
                radius=2,
                color="#b0b0b0",
                weight=1,
                fill=True,
                fill_color="#d3d3d3",
                fill_opacity=0.4,
                popup=f"<b>{node.name}</b><br>ID: {node.stop_id}",
            ).add_to(m)

        trip_colors: dict[str, str] = {}
        palette = ["#d73027", "#fc8d59", "#4575b4", "#91bfdb", "#1a9850", "#fee090"]

        for i, edge in enumerate(path_edges):
            trip = edge.trip_id
            if trip not in trip_colors:
                trip_colors[trip] = palette[len(trip_colors) % len(palette)]

            if i + 1 < len(waypoints):
                seg_start = waypoints[i][:2]
                seg_end = waypoints[i + 1][:2]
            else:
                break

            folium.PolyLine(
                locations=[seg_start, seg_end],
                color=trip_colors[trip],
                weight=5,
                opacity=0.9,
                tooltip=f"{edge.route_name} | {edge.departure_time // 3600:02d}:{(edge.departure_time % 3600) // 60:02d} → {edge.arrival_time // 3600:02d}:{(edge.arrival_time % 3600) // 60:02d}",
            ).add_to(m)

        for idx, (lat, lon, name) in enumerate(waypoints):
            if idx == 0:
                dep_time = f"{path_edges[0].departure_time // 3600:02d}:{(path_edges[0].departure_time % 3600) // 60:02d}"
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.Icon(color="green", icon="flag"),
                    popup=f"<b>▶ СТАРТ</b><br>{name}<br>Отправление: {dep_time}<br>Маршрут: {path_edges[0].route_name}",
                ).add_to(m)
            elif idx == len(waypoints) - 1:
                arr_time = f"{path_edges[-1].arrival_time // 3600:02d}:{(path_edges[-1].arrival_time % 3600) // 60:02d}"
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.Icon(color="red", icon="flag"),
                    popup=f"<b>🏁 ФИНИШ</b><br>{name}<br>Прибытие: {arr_time}",
                ).add_to(m)
            else:
                edge = path_edges[idx - 1]
                arr_time = f"{edge.arrival_time // 3600:02d}:{(edge.arrival_time % 3600) // 60:02d}"

                waiting = 0
                next_trip_mark = ""
                if idx < len(path_edges):
                    next_edge = path_edges[idx]
                    waiting = next_edge.departure_time - edge.arrival_time
                    if edge.trip_id != next_edge.trip_id:
                        next_trip_mark = "<br>✈ Пересадка!"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    color="#333",
                    fill=True,
                    fill_color="#fff",
                    fill_opacity=1.0,
                    popup=f"<b>{name}</b><br>Прибыл: {arr_time}<br>Ожидание: {waiting // 60} мин<br>Маршрут: {edge.route_name}{next_trip_mark}",
                ).add_to(m)

        m.save(str(output_html))
        print(f"Mapa trasy zapisana do: {output_html}", file=sys.stderr)