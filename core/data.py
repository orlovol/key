import csv
from functools import partial
from itertools import chain
from typing import Iterator, NamedTuple, Optional

from . import geo


class Row(NamedTuple):
    geo_id: int
    geo_type: str
    name: str
    name_uk: str


class TreeRow(NamedTuple):
    geo_id: int
    geo_parent_id: int
    geo_type: str
    name: str
    name_uk: str


# ID helpers


def convert_id(i: str) -> Optional[int]:
    """Convert str id into integer/None"""
    return int(i) if i else None


def offset_id(offset: int, id_: int) -> int:
    """Offset negative integer id by offset number"""
    return id_ if id_ > 0 else offset - id_


# CSV I/O


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


# IMPORT


def _read_rows(geo_id: int, geo_type: str, *names: str) -> geo.GeoRecord:
    """Read denormalized csv rows into GeoRecords.
    Data should be sorted by area decreasing"""
    cls = geo.GeoMeta.registry[geo_type]
    record = geo.GeoRecord(geo_id, cls.from_row_record(*names))
    return record


def _read_tree(geo_id: int, geo_parent_id: int, geo_type: str, *names: str) -> geo.GeoRecord:
    """Read tree with parent_id csv rows into GeoRecords.
    Data should be sorted by area decreasing"""
    cls = geo.GeoMeta.registry[geo_type]
    parent = geo.GeoRecord.registry[geo_parent_id] if geo_parent_id else None
    item = cls.from_tree_record(*names, parent=parent)
    record = geo.GeoRecord(geo_id, item)
    return record


def read_items(csv: str) -> Iterator[geo.GeoRecord]:
    rows = read_csv(csv)
    csv_type = next(rows)
    make_record = _read_tree if csv_type == TreeRow else _read_rows
    for row in rows:
        yield make_record(*row)


# EXPORT


def _collect_names(geo_item: geo.GeoItem) -> Iterator[Iterator[str]]:
    """Return lang_name tuples for each level, increasing area size"""
    yield map(str, geo_item)
    while geo_item.parent:
        geo_item = geo_item.parent.item
        yield map(str, geo_item)


def collect_names(geo_item: geo.GeoItem) -> Iterator[str]:
    """Return full names for all languages, decreasing area size"""
    langs = zip(*_collect_names(geo_item))
    return (", ".join(lang[::-1]) for lang in langs)


def _collect_rows(index: dict) -> Iterator[list]:
    """Gather data for csv export as denormalized tree"""
    yield ["geo_id", "geo_type", "name", "name_uk"]
    # count up to nearest hundred frrom max id, and append added items from there
    offset = partial(offset_id, (max(index) // 100 + 1) * 100)
    # sorted by id
    for key in sorted(index, key=offset):
        record = index[key]
        geo_id = offset(record.id)
        geo_item = record.item
        geo_type = geo_item.type
        yield [geo_id, geo_type, *collect_names(geo_item)]


def _collect_tree(index: dict) -> Iterator[list]:
    """Gather data for csv export as tree with parent_id"""
    yield ["geo_id", "geo_parent_id", "geo_type", "name", "name_uk"]
    # count up to nearest hundred frrom max id, and append added items from there
    offset = partial(offset_id, (max(index) // 100 + 1) * 100)
    order = tuple(geo.GeoMeta.registry)
    # sorted by decreasing area
    for key in sorted(index, key=lambda x: order.index(index[x].item.type)):
        record = index[key]
        geo_id = offset(record.id)
        geo_item = record.item
        geo_parent_id = geo_item.parent and offset(geo_item.parent.id)  # can be None
        geo_type = geo_item.type
        yield [geo_id, geo_parent_id, geo_type, *iter(geo_item)]


def write_items(data, path, as_tree):
    collect = _collect_tree if as_tree else _collect_rows
    write_csv(path, collect(data))


__all__ = ["read_items", "write_items"]
