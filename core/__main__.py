import sys
import pathlib

from . import utils, engine

GEOFILE = pathlib.Path(__file__).parent / "data/geo.csv"


@utils.profile
def main():
    interactive = len(sys.argv) > 1
    if not interactive:
        from . import timing  # noqa

    engie = engine.Engine(file=GEOFILE)
    engie.info()

    interactive and engie.interactive()


main()
