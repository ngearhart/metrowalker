from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase, Undefined

@dataclass_json(letter_case=LetterCase.PASCAL, undefined=Undefined.EXCLUDE)
@dataclass
class Station:
    code: str
    name: str
    lat: float
    lon: float
    line_code1: str
    line_code2: str | None
    line_code3: str | None
    line_code4: str | None
    station_together1: str | None
    station_together2: str | None

@dataclass_json(letter_case=LetterCase.PASCAL, undefined=Undefined.EXCLUDE)
@dataclass
class Line:
    display_name: str
    start_station_code: str
    end_station_code: str
    line_code: str


@dataclass_json(letter_case=LetterCase.PASCAL, undefined=Undefined.EXCLUDE)
@dataclass
class MetroPathItem:
    distance_to_prev: int  # feet
    line_code: str
    seq_num: int
    station_code: str
    station_name: str


@dataclass_json(letter_case=LetterCase.PASCAL, undefined=Undefined.EXCLUDE)
@dataclass
class StationToStationInfo:
    composite_miles: float
    source_station: str
    destination_station: str
    rail_time: int  # minutes
