import pprint
from itertools import chain
from tqdm import tqdm
from typing import Iterable, Dict, Set

from . import read, geo, trie, utils


# latin to cyrillic keyboard layout map
keymap_ru = str.maketrans(
    r"qwertyuiop[]asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхъфывапролджэячсмитьбю."
)
keymap_uk = str.maketrans(
    r"qwertyuiop[]\asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхїґфівапролджєячсмитьбю."
)
KEYMAPS = (keymap_uk, keymap_ru)  # ? language preference can be specified somewhere


def read_items(csv):
    for row in read.read_csv(csv):
        geo_id, geo_type, *names = row
        cls = geo.TYPES[geo_type]
        if cls == geo.Street:  # ! ABORT
            return
        item = geo.GeoRecord(int(geo_id), cls.from_texts(*names))
        yield item


class Engine:
    def __init__(self, file=None):
        self._trie = trie.Trie()

        # index of added singleton records, handy alias
        self._index = geo.GeoRecord.registry

        self._parents = {}  # {child_id: one nearest parent_id}
        self._fixup_counter = 0

        self.lookup = self._trie.lookup

        if file:
            items = read_items(file)
            self.index(items)

    def get_parents(self, pathdict: Dict[str, Set[int]]) -> Dict[int, Set[int]]:
        "Return dict of parent ids, grouped by order/geotype level"
        return {
            geo.ORDERS[geotype]: self._trie.lookup(string) for geotype, string in pathdict.items()
        }

    def resolve_parent(self, level_ids: Dict[int, Set[int]]) -> int:
        """Split into lowest and highest parent ids.
        Lookup parents from bottom until we meet the top.
        Return the lowest parent that has the same n-parent as the top id.
        """
        # order geotypes/keys from bottom to top (increasing area)
        *low_levels, top_level = sorted(level_ids, reverse=True)
        top_ids = level_ids[top_level]

        if len(top_ids) > 1:
            raise ValueError(f"Top level has more than one value {top_level}")

        # save lowest level ids, to track their path upward
        paths = {i: i for i in level_ids[low_levels[0]]}

        # find parent ids from lower level ids, moving upwards
        for level in low_levels:
            for k, v in paths.items():
                parent = self._parents.get(v)
                if parent in top_ids:
                    return k
                paths[k] = parent

        # missing some middle path element
        raise ValueError(f"Can't resolve parent from {level_ids}: {paths}")

    @utils.profile
    def index(self, items: Iterable[geo.GeoRecord]) -> None:
        """Add collection of geo items to the trie"""
        for item in tqdm(items):  # * progressbar eats memory, but helps a lot
            self.add(item)

    def add_item(self, item: geo.GeoItem) -> geo.GeoRecord:
        """Convert GeoItem to GeoRecord by creating id and save it"""
        self._fixup_counter -= 1
        record = geo.GeoRecord(id=self._fixup_counter, item=item)
        self._trie.add(record)
        return record

    def add(self, record: geo.GeoRecord):
        """Add GeoRecord to trie and index"""
        self._trie.add(record)

        # * item has parents - GeoItems
        # * check if we have them in index as GeoRecords
        item = record.item
        parent = item.parent  # swappable property, item or record

        while parent:
            if isinstance(parent, geo.GeoRecord):
                # already swapped, go to next
                item = parent.item
                parent = item.parent
                continue

            # * lookup by main lang, regular name
            ids = self._trie.lookup(parent.name.name, exact=True)
            if len(ids) == 0:
                # Parent is not in index, add it
                parent_record = self.add_item(parent)

            elif len(ids) > 1:  # ambiguous match, detect correct parent
                print()
                print(parent, record.name)
                pprint.pprint({i: self._index.get(i) for i in ids})
                pass

            else:
                parent_record = self._index[ids.pop()]

            # * swap geoitem parent with georecord, make it next child
            item.parent = parent = parent_record

        """_COMMENTED_
        # get level-ids dictionary
        level_ids = {}  # ? we should have same path for languages?
        for lang_path in (item.path, item.path_uk):
            ids = self.get_parents(lang_path)
            for k, v in ids.items():
                id_set = level_ids.setdefault(k, set())
                id_set.update(v)

        parent_ids = set(chain.from_iterable(level_ids.values()))
        if len(parent_ids) == 1:
            parent = parent_ids.pop()

        elif level_ids:
            try:
                parent = self.resolve_parent(level_ids)
            except ValueError as e:
                print(f"Unresolved parent: {item.path} {item.name}\n{e}")
                return  # data is batman

        else:  # no parents - no place in index
            return

        # * Add to child-parent id index
        self._parents[item.id] = parent
        """

    # HELPERS

    def info(self):
        info = "\n".join(
            f"{key.title()}: {value}" for key, value in sorted(self._trie.info.items())
        )
        print(f"\n{info}\n")

    def filter(self, results: Set[int]) -> Dict:
        """Filter & format search results"""
        res = {}
        count = total = len(results)
        for r in results:
            obj = self._index[r]
            items = res.setdefault(obj._name, [])
            if len(items) < 3:
                items.append(obj)
                count -= 1

        if count:
            res["~more~"] = count
        res["~total~"] = total
        return res

    def interactive(self):
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

            # * sorted alphabeticatlly =(
            pprint.pprint(self.filter(res))

        print("Bye!")
