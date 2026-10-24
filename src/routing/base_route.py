from __future__ import annotations

from abc import ABC
from math import atan2, cos, radians, sin, sqrt

from ..graph.graph import GTFSGraph


class BaseRouteFinder(ABC):
    def __init__(self, graph: GTFSGraph):
        self.graph = graph

    def _haversine_m(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r * c