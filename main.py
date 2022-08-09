
from collections import defaultdict
import requests
from typing import List
import networkx
from functools import cached_property, cache
from matplotlib import pyplot
from pprint import pprint

from data import Line, MetroPathItem, Station, StationToStationInfo

COLORS = {
    'RD': '#f44336',
    'BL': '#2986cc',
    'YL': '#81ff66',
    'OR': '#ce7e00',
    'GR': '#8fce00',
    'SV': '#bcbcbc'
}

STATION_TRANSFER_PENALTY_MINUTES = 10


@cache
def get_api_key():
    with open('api_key.txt', 'r') as file:
        return file.readlines()[0]


class MetroGraph(networkx.Graph):

    def __init__(self):
        super().__init__()
        response = requests.get(
            'https://api.wmata.com/Rail.svc/json/jStations',
            headers={
                'api_key': get_api_key()
            }
        ).json()
        self.station_list = Station.schema().load(response['Stations'], many=True)
        for station in self.station_list:
            self.add_node(station.code)
        self._build_edges()

    def get_station(self, code: str) -> Station:
        return next(station for station in self.station_list if station.code == code)

    def _build_edges(self):
        response = requests.get(
            'https://api.wmata.com/Rail.svc/json/jLines',
            headers={
                'api_key': get_api_key()
            }
        ).json()
        self.line_list = Line.schema().load(response['Lines'], many=True)

        # Retrieve estimated time to go between stations (for weights)
        weights = self._build_weights()
        for line in self.line_list:
            self._traverse_line(line, weights)
        # Add edge of small weight between stations that are the same
        for station in self.station_list:
            if station.station_together1 is not None and len(station.station_together1) > 0:
                self.add_edge(
                    station.code,
                    station.station_together1,
                    weight=STATION_TRANSFER_PENALTY_MINUTES # Incur a small cost to switch platforms
                )
            if station.station_together2 is not None  and len(station.station_together2) > 0:
                self.add_edge(
                    station.code,
                    station.station_together2,
                    weight=STATION_TRANSFER_PENALTY_MINUTES
                )

    def _build_weights(self) -> dict:
        response = requests.get(
            'https://api.wmata.com/Rail.svc/json/jSrcStationToDstStationInfo',
            headers={
                'api_key': get_api_key()
            }
        ).json()
        self.station_to_station_list = StationToStationInfo.schema().load(response['StationToStationInfos'], many=True)
        result = defaultdict(dict)
        for station_info in self.station_to_station_list:
            result[station_info.source_station][station_info.destination_station] = station_info.rail_time
            result[station_info.destination_station][station_info.source_station] = station_info.rail_time
        return result

    def _traverse_line(self, line: Line, weights: dict):
        response = requests.get(
            f'https://api.wmata.com/Rail.svc/json/jPath?FromStationCode={line.start_station_code}&ToStationCode={line.end_station_code}',
            headers={
                'api_key': get_api_key()
            }
        ).json()
        path = MetroPathItem.schema().load(response['Path'], many=True)
        previous_station = path[0]
        for next_station in path[1:]:
            self.add_edge(
                previous_station.station_code,
                next_station.station_code,
                weight=weights[previous_station.station_code][next_station.station_code]
                # weight=next_station.distance_to_prev
            )
            previous_station = next_station

    @cached_property
    def positions(self):
        return {station.code: (station.lon, station.lat) for station in self.station_list}

    @cached_property
    def vertex_labels(self):
        return {station.code: station.name for station in self.station_list}

    @cached_property
    def vertext_colors(self):
        return [COLORS[station.line_code1] for station in self.station_list]

    def show(self):
        networkx.draw(self, pos=self.positions, labels=self.vertex_labels, node_color=self.vertext_colors, font_size=8)
        pyplot.show()

    def traveling_salesman(self):
        return networkx.approximation.traveling_salesman_problem(self, cycle=False)

g = MetroGraph()
result = g.traveling_salesman()
print('Result:')
pprint([g.get_station(station).name for station in result if len(station) > 0], width=80, compact=True)

total_minutes = networkx.path_weight(g, result, weight="weight")
print(f'Total minutes: {total_minutes} = {total_minutes / 60} hours')
# g.show()
