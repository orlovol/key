from . import parse

geofile = "geo.csv"

for row in parse.read_csv(geofile):
    print(row)
