from __future__ import annotations
from typing import Dict, List, Literal, cast
from dataclasses import replace

import pandas as pd
import geopandas as gpd
from intervaltree import IntervalTree
from datetime import datetime, date
from src.loader import GTFSData
from src.loader.constants import (
    RoutesCol,
    StopsCol,
    StopTimesCol,
    TripsCol,
    CalendarCol,
    
)
from .node import StopNode
from .edge import RouteEdge
from .types import IdStop, DayOfWeek, IdSevice

class GTFSGraph:
    def __init__(self, data: GTFSData) -> None:
        self.nodes: Dict[IdStop, StopNode] = {}
        self.services_by_day_of_week: Dict[DayOfWeek, set[IdSevice]] = cast(
            Dict[DayOfWeek, set[IdSevice]],
            {day: set() for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}
        )
        self.service_id_by_dates_range: IntervalTree = IntervalTree()
        
        self._build_nodes(data.stops)
        self._build_edges(data)
        self._build_calendar(data.calendar)


    def _build_nodes(self, stops_gdf: gpd.GeoDataFrame) -> None:
        for _, row in stops_gdf.iterrows():
            stop_id = str(row[StopsCol.ID.value.name])
            parent_id = None if row['location_type'] == 1 else (str(row[StopsCol.PARENT_STATION.value.name]))

            if parent_id is None:
                if(stop_id in self.nodes):
                    raise ValueError(f"Duplicate stop_id found: {stop_id}")
                self.nodes[stop_id] = StopNode(
                    stop_id=stop_id,
                    name=row[StopsCol.NAME.value.name],
                    point=row["geometry"],
                ) 
            else:
                if (parent_id in self.nodes):
                    self.nodes[stop_id] = self.nodes[parent_id]
                else:
                    raise ValueError(f"Parent station {parent_id} for stop {stop_id} not found in nodes")       
                  
    def _build_calendar(self, calendar_df: pd.DataFrame) -> None:
        days_of_week: List[DayOfWeek] = cast(
            List[DayOfWeek],
            [
                CalendarCol.MONDAY.value.name,
                CalendarCol.TUESDAY.value.name,
                CalendarCol.WEDNESDAY.value.name,
                CalendarCol.THURSDAY.value.name,
                CalendarCol.FRIDAY.value.name,
                CalendarCol.SATURDAY.value.name,
                CalendarCol.SUNDAY.value.name,
            ]
        )

        for _, row in calendar_df.iterrows():
            service_id = str(row[CalendarCol.SERVICE_ID.value.name])
            start_date = int(row[CalendarCol.START_DATE.value.name]) 
            end_date = int(row[CalendarCol.END_DATE.value.name])      
            self.service_id_by_dates_range[start_date:end_date+1] = service_id
            
            for day in days_of_week:
                if row[day] == 1:
                    self.services_by_day_of_week[day].add(service_id)

    def _build_edges(self, data: GTFSData) -> None:
        routes_info = data.routes[[RoutesCol.ID.value.name, RoutesCol.SHORT_NAME.value.name, RoutesCol.LONG_NAME.value.name]].copy()
        routes_info["route_name"] = routes_info[RoutesCol.SHORT_NAME.value.name].fillna(routes_info[RoutesCol.LONG_NAME.value.name])

   

        trips_with_routes = data.trips[[TripsCol.ID.value.name, TripsCol.ROUTE_ID.value.name, TripsCol.SERVICE_ID.value.name]].merge(
            routes_info[[RoutesCol.ID.value.name, "route_name"]],
            left_on=TripsCol.ROUTE_ID.value.name,
            right_on=RoutesCol.ID.value.name,
            how="left",
        ).copy()

        full_df = data.stop_times[[StopTimesCol.TRIP_ID.value.name, StopTimesCol.STOP_ID.value.name, StopTimesCol.STOP_SEQ.value.name, StopTimesCol.DEP_TIME.value.name, StopTimesCol.ARR_TIME.value.name]].merge(
        trips_with_routes[[TripsCol.ID.value.name, "route_name", TripsCol.SERVICE_ID.value.name]],
        left_on=StopTimesCol.TRIP_ID.value.name,
        right_on=TripsCol.ID.value.name,
        how="left").copy()

        full_df = full_df.sort_values(by=[
            StopTimesCol.TRIP_ID.value.name,
            StopTimesCol.STOP_SEQ.value.name
        ])
        
        cols = [
            StopTimesCol.TRIP_ID.value.name,      
            StopTimesCol.STOP_ID.value.name,      
            StopTimesCol.DEP_TIME.value.name,     
            StopTimesCol.ARR_TIME.value.name,    
            "route_name",
            TripsCol.SERVICE_ID.value.name,       
        ]

        prev_trip_id = None
        prev_stop_id = None
        prev_dep = None
        prev_line = None
        prev_service = None

        for trip_id, stop_id, dep, arr, route_name, service_id in full_df[cols].itertuples(index=False, name=None):
            if prev_trip_id is not None and trip_id == prev_trip_id:

                u_node_id = str(prev_stop_id)
                v_node_id = str(stop_id)

                if u_node_id in self.nodes:
                    u_node = self.nodes[u_node_id]
                else:
                    raise ValueError(f"Stop {u_node_id} not found")


                if v_node_id in self.nodes: 
                    v_node = self.nodes[v_node_id]
                else:
                    raise ValueError(f"Stop {v_node_id} not found")
                
                if(prev_dep is None or arr is None or route_name is None or service_id is None):
                    raise ValueError(f"Missing data for edge: dep={dep}, arr={arr}, line_name={route_name}, service_id={service_id}")

                u_node.add_transit_edge(RouteEdge(
                    target=v_node,
                    departure_time=int(prev_dep),
                    arrival_time=int(arr),
                    route_name=route_name,
                    service_id=service_id,
                    trip_id=trip_id,
                    distance_m=u_node.point.distance(v_node.point) * 111320) #TODO исправить на номральный подсчет
                )

            prev_trip_id = trip_id
            prev_stop_id = stop_id
            prev_dep = dep
            prev_line = route_name
            prev_service = service_id

    def get_services_for_date(self, target_date: date) -> set[IdSevice]:
        day_of_week = target_date.strftime("%A").lower() #TODO может быть стоит сделать мапу для надежности
        if day_of_week not in self.services_by_day_of_week:
            raise ValueError(f"Invalid day of week: {day_of_week}")
        
        active_services_id = self._get_active_services_for_date(target_date, cast(DayOfWeek, day_of_week))
        return active_services_id
    
    def _get_active_services_for_date(self, target_date: date, day_of_week: DayOfWeek) -> set[IdSevice]:
        target_date_int = int(target_date.strftime("%Y%m%d"))
        intervals = self.service_id_by_dates_range[target_date_int]
        date_services = {interval.data for interval in intervals}  # ← используем .data
        day_services = self.services_by_day_of_week[day_of_week]
        active_services_id = date_services & day_services
        return active_services_id
    
    def get_filtered_nodes_for_date(self, target_date: date) -> Dict[IdStop, StopNode]:
        
        active_services_id: set[IdSevice] = self.get_services_for_date(target_date)
        filtered_nodes: Dict[IdStop, StopNode] = {}
        for stop_id, original_node in self.nodes.items():
            filtered_nodes[stop_id] = replace(original_node, edges=[]) #TODO не прям полная копия
    
        for stop_id, original_node in self.nodes.items():
            for edge in original_node.edges:
                if edge.service_id in active_services_id:
                    new_edge = replace(edge, target=filtered_nodes[edge.target.stop_id])
                    filtered_nodes[stop_id].add_transit_edge(new_edge)
        
        return filtered_nodes

    def get_node(self, stop_id: str) -> StopNode | None:
        return self.nodes.get(stop_id)

    def neighbors(self, stop_id: str) -> List[RouteEdge] | None:
        node = self.nodes.get(stop_id)
        return node.edges if node else None

    def get_neighbors_after(self, stop_id: str, min_dep_time: int) -> List[RouteEdge] | None:
        edges = self.neighbors(stop_id)
        if edges is None:
            return None
        return [e for e in edges if e.departure_time >= min_dep_time]

    def __repr__(self) -> str:
        total_edges = sum(len(n.edges) for n in self.nodes.values())
        return f"GTFSGraph(nodes={len(self.nodes)}, edges≈{total_edges})"