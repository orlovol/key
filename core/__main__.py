from . import parse, geo

geofile = "geo.csv"

for row in parse.read_csv(geofile):
    if isinstance(row, (geo.Region, geo.Raion)):
        print(row)

from pprint import pprint
pprint(geo.Region.registry)
pprint(geo.Raion.registry)