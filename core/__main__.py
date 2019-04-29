import sys
import argparse

from . import engine, utils


class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


@utils.profile
def main():

    parser = DefaultHelpParser(description="Key Search Engine.")
    parser.add_argument("infile", help="input .csv file with geodata")
    parser.add_argument(
        "-e",
        "--export",
        choices=["tree", "csv"],
        help="export data into output file in specified format",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="exported.csv",
        help="output file where exported data is saved (default: exported.csv)",
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="run in interactive query mode"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="output detailed info")

    args = parser.parse_args()

    if not args.interactive:
        from . import timing  # noqa

    engie = engine.Engine(file=args.infile)
    if args.verbose:
        engie.info()

    if args.export:
        engie.export(args.output, as_tree=args.export == "tree")

    if args.interactive:
        engie.interactive()


main()
