import csv
import typing


class Row(typing.NamedTuple):
    geo_id: int
    geo_type: str
    name: str
    name_uk: str


def row_maker(row):
    try:
        return Row._make(row)
    except TypeError as e:
        raise ValueError(f"Invalid row: {row}") from e


def read_csv(path):
    with open(path, newline="") as data:
        data.readline()  # skip header
        georeader = csv.reader(data, escapechar="\\")
        for row in map(row_maker, georeader):
            yield row
