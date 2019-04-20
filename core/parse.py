import csv
import typing

from . import geo


class Row(typing.NamedTuple):
    geo_id: int
    geo_type: str
    name: str
    name_uk: str

    @classmethod
    def parse(cls, row):
        geo_id, geo_type, *names = row
        try:
            geocls = geo.TYPES[geo_type]
            return geocls(int(geo_id), *names)
        except:  # unsupported GeoItem, default to simple Row
            return cls(*row)


def read_csv(path):
    with open(path, newline="") as data:
        data.readline()  # skip header
        georeader = csv.reader(data)
        for row in map(Row.parse, georeader):
            yield row
