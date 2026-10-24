from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, Literal, Type

import geopandas as gpd
import pandas as pd

from .constants import (
    GTFSColumn,
    GTFSFile,
    StopsCol,
    StopTimesCol,
)


class GTFSLoaderError(Exception):
    pass


class GTFSFileMissingError(GTFSLoaderError):
    pass


class GTFSMissingColumnError(GTFSLoaderError):
    pass


class GTFSMissingDependencyError(GTFSLoaderError):
    pass


@dataclass
class GTFSData:
    agency: pd.DataFrame
    stops: gpd.GeoDataFrame
    stop_times: pd.DataFrame
    trips: pd.DataFrame
    calendar: pd.DataFrame
    calendar_dates: pd.DataFrame
    routes: pd.DataFrame
    feed_info: pd.DataFrame


class GTFSDataLoader:
    data_dir: Path
    _data: GTFSData | None

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = self._resolve_data_dir(data_dir)
        self._data = None

    def _resolve_data_dir(self, data_dir: str | Path) -> Path:
        resolved_path = Path(data_dir)
        if resolved_path.exists() and resolved_path.is_dir():
            return resolved_path

        raise GTFSLoaderError(f"Nie znaleziono katalogu z danymi: {resolved_path}")

    @property
    def data(self) -> GTFSData:
        if self._data is None:
            raise GTFSLoaderError("Dane nie zostaly jeszcze zaladowane. Wywolaj load().")
        return self._data

    def load(self) -> GTFSData:
        dfs: Dict[GTFSFile, pd.DataFrame] = {}

        for gtfs_file in GTFSFile:
            df = self._load_single_file(gtfs_file)
            self._validate_columns(df, gtfs_file)
            df = self._cast_columns(df, gtfs_file)
            dfs[gtfs_file] = df

        stops_df = dfs[GTFSFile.STOPS]
        stops_gdf = self._build_stops_geodataframe(stops_df, GTFSFile.STOPS)

        self._data = GTFSData(
            agency=dfs[GTFSFile.AGENCY],
            stops=stops_gdf,
            stop_times=dfs[GTFSFile.STOP_TIMES],
            trips=dfs[GTFSFile.TRIPS],
            calendar=dfs[GTFSFile.CALENDAR],
            calendar_dates=dfs[GTFSFile.CALENDAR_DATES],
            routes=dfs[GTFSFile.ROUTES],
            feed_info=dfs[GTFSFile.FEED_INFO],
        )

        return self._data

    def _load_single_file(self, gtfs_file: GTFSFile) -> pd.DataFrame:
        path = self.data_dir / gtfs_file.value[0]
        if not path.exists():
            raise GTFSFileMissingError(f"Nie znaleziono pliku {gtfs_file.value[0]} w {self.data_dir}")

        try:
            df = pd.read_csv(path, dtype=str)
        except Exception as exc:  # noqa: BLE001
            raise GTFSLoaderError(f"Blad podczas odczytu pliku {path}: {exc}") from exc

        return df

    def _validate_columns(self, df: pd.DataFrame, gtfs_file: GTFSFile) -> None:
        required_columns = {column.value.name for column in gtfs_file.value[1]}
        missing = required_columns - set(df.columns)
        if missing:
            raise GTFSMissingColumnError(
                f"W pliku {gtfs_file.value[0]} brakuje kolumn: {sorted(missing)}. "
                "Sprawdz naglowki i constants.py."
            )

    def _cast_columns(self, df: pd.DataFrame, gtfs_file: GTFSFile) -> pd.DataFrame:
        typed_df = df.copy()

        for column in gtfs_file.value[1]:
            column_value = column.value
            try:
                typed_df[column_value.name] = self._cast_column(typed_df[column_value.name], column)
            except (TypeError, ValueError) as exc:
                raise GTFSLoaderError(
                    f"Nie udalo sie przekonwertowac kolumny {column_value.name} "
                    f"w pliku {gtfs_file.value[0]} na typ {column_value.dtype}: {exc}"
                ) from exc

        return typed_df

    def _cast_column(self, series: pd.Series, column: Enum) -> pd.Series:
        if column in {StopTimesCol.ARR_TIME, StopTimesCol.DEP_TIME}:
            return self._parse_gtfs_time(series)

        return series.astype(column.value.dtype)

    def _parse_gtfs_time(self, series: pd.Series) -> pd.Series:
        raw = series.astype("string")
        parts = raw.str.extract(r"^(?P<hours>\d+):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)$")

        invalid_mask = raw.notna() & parts.isna().any(axis=1)
        if invalid_mask.any():
            invalid_values = raw[invalid_mask].dropna().unique().tolist()
            raise ValueError(f"Niepoprawny format czasu GTFS: {invalid_values[:5]}")

        hours = pd.to_numeric(parts["hours"], errors="coerce")
        minutes = pd.to_numeric(parts["minutes"], errors="coerce")
        seconds = pd.to_numeric(parts["seconds"], errors="coerce")
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds.astype("Int64")

    def _build_stops_geodataframe(self, stops_df: pd.DataFrame, gtfs_file: Literal[GTFSFile.STOPS]) -> gpd.GeoDataFrame:
        lon_col = gtfs_file.value[1].LON.value.name
        lat_col = gtfs_file.value[1].LAT.value.name
        
        lon = pd.to_numeric(stops_df[lon_col], errors="coerce")
        lat = pd.to_numeric(stops_df[lat_col], errors="coerce")
        valid_mask = lon.notna() & lat.notna()

        if not valid_mask.any():
            raise GTFSLoaderError(
                "W stops.txt nie znaleziono ani jednej poprawnej pary "
                "wspolrzednych stop_lon/stop_lat."
            )

        stops_work = stops_df.copy()
        stops_work[lon_col] = lon
        stops_work[lat_col] = lat

        geometry = gpd.points_from_xy(stops_work[lon_col], stops_work[lat_col])
        stops_gdf = gpd.GeoDataFrame(stops_work, geometry=geometry, crs="EPSG:4326")

        if (~valid_mask).any():
            stops_gdf.loc[~valid_mask, "geometry"] = None

        return stops_gdf