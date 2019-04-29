import csv
import typing
from itertools import chain
from functools import partial


class Row(typing.NamedTuple):
    geo_id: int
    geo_type: str
    name: str
    name_uk: str


class TreeRow(typing.NamedTuple):
    geo_id: int
    geo_parent_id: int
    geo_type: str
    name: str
    name_uk: str


def convert_id(i: str) -> typing.Optional[int]:
    return int(i) if i else None


def _row_maker(cls, row):
    ids = 2 if cls == TreeRow else 1
    row = chain(map(convert_id, row[:ids]), row[ids:])
    try:
        return cls._make(row)
    except TypeError as e:
        raise ValueError(f"Invalid row: {row}") from e


def read_csv(path):
    with open(path, newline="") as data:
        header = data.readline()
        cls = TreeRow if "geo_parent_id" in header else Row
        yield cls  # first item is type of csv file we're reading

        row_maker = partial(_row_maker, cls)
        georeader = csv.reader(data, escapechar="\\")
        for row in map(row_maker, georeader):
            yield row


def write_csv(path, data):
    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(
            csvfile, escapechar="\\", doublequote=False, quoting=csv.QUOTE_NONNUMERIC
        )
        for row in data:
            writer.writerow(row)
