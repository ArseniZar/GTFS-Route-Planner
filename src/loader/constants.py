from dataclasses import dataclass
from enum import Enum
from typing import Literal, Mapping, TypeAlias


GTFSDType: TypeAlias = Literal["string", "Int64", "Float64"]


@dataclass(frozen=True)
class GTFSColumn:
    name: str
    dtype: GTFSDType


class AgencyCol(Enum):
    ID = GTFSColumn("agency_id", "string")
    NAME = GTFSColumn("agency_name", "string")
    URL = GTFSColumn("agency_url", "string")
    TIMEZONE = GTFSColumn("agency_timezone", "string")
    PHONE = GTFSColumn("agency_phone", "string")
    EMAIL = GTFSColumn("agency_email", "string")
    FARE_URL = GTFSColumn("agency_fare_url", "string")


class StopsCol(Enum):
    ID = GTFSColumn("stop_id", "string")
    CODE = GTFSColumn("stop_code", "string")
    NAME = GTFSColumn("stop_name", "string")
    DESC = GTFSColumn("stop_desc", "string")
    LAT = GTFSColumn("stop_lat", "Float64")
    LON = GTFSColumn("stop_lon", "Float64")
    LOCATION_TYPE = GTFSColumn("location_type", "Int64")
    PARENT_STATION = GTFSColumn("parent_station", "string")
    PLATFORM_CODE = GTFSColumn("platform_code", "string")


class StopTimesCol(Enum):
    TRIP_ID = GTFSColumn("trip_id", "string")
    ARR_TIME = GTFSColumn("arrival_time", "Int64")
    DEP_TIME = GTFSColumn("departure_time", "Int64")
    STOP_ID = GTFSColumn("stop_id", "string")
    STOP_SEQ = GTFSColumn("stop_sequence", "Int64")
    HEADSIGN = GTFSColumn("stop_headsign", "string")
    PICKUP_TYPE = GTFSColumn("pickup_type", "Int64")
    SHAPE_DIST = GTFSColumn("shape_dist_traveled", "Float64")


class TripsCol(Enum):
    ROUTE_ID = GTFSColumn("route_id", "string")
    SERVICE_ID = GTFSColumn("service_id", "string")
    ID = GTFSColumn("trip_id", "string")
    HEADSIGN = GTFSColumn("trip_headsign", "string")
    DIRECTION_ID = GTFSColumn("direction_id", "Int64")
    BLOCK_ID = GTFSColumn("block_id", "string")


class CalendarCol(Enum):
    SERVICE_ID = GTFSColumn("service_id", "string")
    MONDAY = GTFSColumn("monday", "Int64")
    TUESDAY = GTFSColumn("tuesday", "Int64")
    WEDNESDAY = GTFSColumn("wednesday", "Int64")
    THURSDAY = GTFSColumn("thursday", "Int64")
    FRIDAY = GTFSColumn("friday", "Int64")
    SATURDAY = GTFSColumn("saturday", "Int64")
    SUNDAY = GTFSColumn("sunday", "Int64")
    START_DATE = GTFSColumn("start_date", "string")
    END_DATE = GTFSColumn("end_date", "string")


class CalendarDatesCol(Enum):
    SERVICE_ID = GTFSColumn("service_id", "string")
    DATE = GTFSColumn("date", "string")
    EXCEPTION_TYPE = GTFSColumn("exception_type", "Int64")


class RoutesCol(Enum):
    ID = GTFSColumn("route_id", "string")
    AGENCY_ID = GTFSColumn("agency_id", "string")
    SHORT_NAME = GTFSColumn("route_short_name", "string")
    LONG_NAME = GTFSColumn("route_long_name", "string")
    TYPE = GTFSColumn("route_type", "Int64")
    COLOR = GTFSColumn("route_color", "string")
    TEXT_COLOR = GTFSColumn("route_text_color", "string")


class FeedInfoCol(Enum):
    PUBLISHER_NAME = GTFSColumn("feed_publisher_name", "string")
    PUBLISHER_URL = GTFSColumn("feed_publisher_url", "string")
    LANG = GTFSColumn("feed_lang", "string")
    START_DATE = GTFSColumn("feed_start_date", "string")
    END_DATE = GTFSColumn("feed_end_date", "string")


class GTFSFile(Enum):
    AGENCY = ("agency.txt", AgencyCol)
    STOPS = ("stops.txt", StopsCol)
    STOP_TIMES = ("stop_times.txt", StopTimesCol)
    TRIPS = ("trips.txt", TripsCol)
    CALENDAR = ("calendar.txt", CalendarCol)
    CALENDAR_DATES = ("calendar_dates.txt", CalendarDatesCol)
    ROUTES = ("routes.txt", RoutesCol)
    FEED_INFO = ("feed_info.txt", FeedInfoCol)