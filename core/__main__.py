import sys
import pathlib
from tqdm import tqdm
from pprint import pprint
from typing import Iterable

from . import read, geo, trie, utils

# latin to cyrillic keyboard layout map
keymap_ru = str.maketrans(
    r"qwertyuiop[]asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхъфывапролджэячсмитьбю."
)
keymap_uk = str.maketrans(
    r"qwertyuiop[]\asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхїґфівапролджєячсмитьбю."
)
KEYMAPS = (keymap_uk, keymap_ru)  # ? language preference can be specified somewhere
GEOFILE = pathlib.Path(__file__).parent / "data/geo.csv"


def read_items(csv):
    for row in read.read_csv(csv):
        geo_id, geo_type, *names = row
        try:
            geocls = geo.TYPES[geo_type]
            geo_obj = geocls(int(geo_id), *names)
            yield geo_obj
        except Exception as e:  # unsupported GeoItem, default to simple Row
            print(e)


class Engine:
    def __init__(self, items):
        self._trie = trie.Trie()
        self._index = {}

        self.lookup = self._trie.lookup

        if items:
            self.index(items)

    @utils.profile
    def index(self, items: Iterable[geo.GeoItem]) -> None:
        """Add collection of geo items to the trie"""
        for item in tqdm(items):  # * progressbar eats memory, but helps a lot
            self.add(item)

    def add(self, item):
        self._trie.add(item)

        # get parent ids and add to them
        if item._name == "city":
            for lang_path in (item.path, item.path_uk):
                parent_ids = set()
                for key in geo.TYPES.keys():  # ordered top-bottom lookup
                    try:
                        path = lang_path[key]
                    except KeyError:
                        # no parent level for this key, it's okay
                        continue
                    else:
                        ids = self._trie.lookup(path)
                        parent_ids |= ids

        # ! flat index for now, TODO: nested index
        self._index[item.geo_id] = item

    def info(self):
        info = "\n".join(
            f"{key.title()}: {value}" for key, value in sorted(self._trie.info.items())
        )
        print(f"\n{info}\n")

    def repl(self):
        query = "Enter query (empty to exit):"
        print(query)
        while query:
            try:
                query = input("> ")
            except (EOFError, KeyboardInterrupt):
                break

            if not query:
                continue

            res = self.lookup(query)
            if not res:
                for m in KEYMAPS:
                    tr = query.translate(m)
                    res = self.lookup(tr)
                    if res:
                        print(f"Did you mean _{tr}_?")
                        break
            pprint([self._index[r] for r in res])

        print("Bye!")


@utils.profile
def main():
    interactive = len(sys.argv) > 1
    if not interactive:
        from . import timing  # noqa

    engine = Engine(items=read_items(GEOFILE))
    engine.info()

    if interactive:
        engine.repl()


main()
