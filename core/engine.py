import pprint
from tqdm import tqdm
from typing import Any, Iterable, Dict, Set

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
            self.index(read_items(file))

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

    def search(self, name: str, ids: Set[int]) -> int:
        """Find id by exact name in subset of ids"""
        records = [self._index.get(i) for i in ids]
        for record in records:
            if record.item.name.name == name:
                return record
        raise KeyError(f'Name "{name}" was not found in the records: {records}')

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
            query = parent.name.name
            ids = self._trie.lookup(query, exact=True)
            if len(ids) == 0:
                # Parent is not in index, add it
                parent_record = self.add_item(parent)

            elif len(ids) > 1:
                # Ambiguous match, detect correct parent.
                # Most often word "superset" is matched, because names are split
                # into many words: "aaa-bbb": "aaa", "bbb"
                # Search by full name from index
                try:
                    parent_record = self.search(query, ids)
                except KeyError:
                    # multiple parents and yet we don't have the one we need
                    # let's add it, whatever it is
                    parent_record = self.add_item(parent)

            else:
                parent_record = self._index[ids.pop()]

            # * swap geoitem parent with georecord, make it next child
            item.parent = parent = parent_record

    # HELPERS

    def info(self):
        info = "\n".join(
            f"{key.title()}: {value}" for key, value in sorted(self._trie.info.items())
        )
        print(f"\n{info}\n")

    def filter(self, results: Set[int], maxcount=3) -> Dict:
        """Filter & format search results"""
        res: Dict[str, Any] = {}
        count = total = len(results)
        for r in results:
            obj = self._index[r]
            items = res.setdefault(obj.item._name, [])
            if len(items) < maxcount:
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
            pprint.pprint(self.filter(res, 3))

        print("Bye!")
