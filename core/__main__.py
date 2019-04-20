import sys
import pathlib
from pprint import pprint

from . import parse, trie, utils

# latin to cyrillic keyboard layout map
keymap = str.maketrans(r"qwertyuiop[]asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхъфывапролджэячсмитьбю.")

keymap_uk = str.maketrans(
    r"qwertyuiop[]\asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхїґфівапролджєячсмитьбю."
)

# * language prefernce might be specified somewhere
keymaps = (keymap_uk, keymap)


def repl(lookup, items):
    query = "Enter query (empty to exit):"
    print(query)
    while query:
        try:
            query = input("> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not query:
            continue

        res = lookup(query)
        if not res:
            for m in keymaps:
                tr = query.translate(m)
                res = lookup(tr)
                if res:
                    print(f"Did you mean _{tr}_?")
                    break
        print([items[r] for r in res])

    print("Bye!")


def iter_items():
    geofile = pathlib.Path(__file__).parent / "data/geo.csv"
    for row in parse.read_csv(geofile):
        yield row


@utils.profile
def main():
    interactive = len(sys.argv) > 1
    if not interactive:
        from . import timing  # noqa

    geotrie = trie.Trie()

    items = list(iter_items())  # * used twice, so wrap in list
    # pprint(items)
    geotrie.index(items)
    # ! FIXME: use readable name for repl, but whole record for output
    # ! FIXME: optimize index/registry usages
    geoindex = {item.geo_id: item for item in items}

    info = "\n".join(f"{key.title()}: {value}" for key, value in sorted(geotrie.info.items()))
    print(f"\n{info}\n")

    # # geotrie.show()
    if interactive:
        repl(geotrie.lookup, geoindex)

    # pprint(geoindex)
    # pprint(geo.Region.registry)


# TODO: add parents to objects
# TODO: add geotype to trie, search for old name only

main()
