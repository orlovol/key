import csv
import typing


class Row(typing.NamedTuple):
    geo_id: int
    geo_type: str
    name: str
    name_uk: str


def read_csv(path):
    with open(path, newline="") as data:
        data.readline()  # skip header
        georeader = csv.reader(data)
        for row in map(Row._make, georeader):
            yield row


if __name__ == "__main__":
    geofile = "geo.csv"

    for row in read_csv(geofile):
        print(row)
