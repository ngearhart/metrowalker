
import requests
from typing import List
import networkx
from functools import cached_property
from matplotlib import pyplot

from data import Line, MetroPathItem, Station

COLORS = {
    'RD': '#f44336',
    'BL': '#2986cc',
    'YL': '#81ff66',
    'OR': '#ce7e00',
    'GR': '#8fce00',
    'SV': '#bcbcbc'
}


class MetroGraph(networkx.Graph):

    def __init__(self):
        super().__init__()
        response = requests.get(
            'https://api.wmata.com/Rail.svc/json/jStations',
            headers={
                'api_key': '7a74e104f95940c7b4dc8afdb466fd61'
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
                'api_key': '7a74e104f95940c7b4dc8afdb466fd61'
            }
        ).json()
        self.line_list = Line.schema().load(response['Lines'], many=True)
        for line in self.line_list:
            self._traverse_line(line)
        # Add edge of weight 0 between stations that are the same
        for station in self.station_list:
            if station.station_together1 is not None:
                self.add_edge(
                    station.code,
                    station.station_together1,
                    weight=0
                )
            if station.station_together2 is not None:
                self.add_edge(
                    station.code,
                    station.station_together2,
                    weight=0
                )

    def _traverse_line(self, line: Line):
        response = requests.get(
            f'https://api.wmata.com/Rail.svc/json/jPath?FromStationCode={line.start_station_code}&ToStationCode={line.end_station_code}',
            headers={
                'api_key': '7a74e104f95940c7b4dc8afdb466fd61'
            }
        ).json()
        path = MetroPathItem.schema().load(response['Path'], many=True)
        previous_station = path[0]
        for next_station in path[1:]:
            self.add_edge(
                previous_station.station_code,
                next_station.station_code,
                weight=next_station.distance_to_prev
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
        result = networkx.approximation.traveling_salesman_problem(self, cycle=False)
        return result
        # return [self.get_station(station).name for station in result]

g = MetroGraph()
print(g.traveling_salesman())
