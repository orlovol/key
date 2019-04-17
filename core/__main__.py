from pprint import pprint

from . import parse, geo


geofile = "geo.csv"

for row in parse.read_csv(geofile):
    if isinstance(row, (geo.City,)):
        print(row, row.regname) # FIXME: wrong tree
    pass

pprint(geo.Region.registry)
pprint(geo.Raion.registry)