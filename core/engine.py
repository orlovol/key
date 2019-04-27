from tqdm import tqdm
from typing import Any, Iterable, Dict, Set, Iterator, List

from . import data, geo, trie, utils


# latin to cyrillic keyboard layout map
keymap_ru = str.maketrans(
    r"qwertyuiop[]asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхъфывапролджэячсмитьбю."
)
keymap_uk = str.maketrans(
    r"qwertyuiop[]\asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхїґфівапролджєячсмитьбю."
)
KEYMAPS = (keymap_uk, keymap_ru)  # ? language preference can be specified somewhere


def _collect_names(geo_item: geo.GeoItem) -> Iterator[Iterator[str]]:
    """Return lang_name tuples for each level, increasing area size"""
    yield map(str, geo_item)
    while geo_item.parent:
        if isinstance(geo_item.parent, geo.GeoRecord):
            geo_item = geo_item.parent.item
        else:
            geo_item = geo_item.parent
        yield map(str, geo_item)


def collect_names(geo_item: geo.GeoItem) -> Iterator[str]:
    """Return full names for all languages, decreasing area size"""
    langs = zip(*_collect_names(geo_item))
    return (", ".join(lang[::-1]) for lang in langs)


def collect_data(index: dict) -> Iterator[List[str]]:
    """Gather data rows for csv export"""
    yield ["geo_id", "geo_type", "name", "name_uk"]
    max_id = max(index)
    # count up to nearest hundred
    offset = (max_id // 100 + 1) * 100
    offset_id = lambda id_: id_ if id_ > 0 else offset - id_

    for key in sorted(index, key=offset_id):
        record = index[key]
        geo_id = offset_id(record.id)
        geo_item = record.item
        geo_type = geo_item._type
        yield [geo_id, geo_type, *collect_names(geo_item)]


def same_parents(child: geo.GeoItem, possible_sibling: geo.GeoItem) -> bool:
    """Check if two items have the same parent. Should have similar names"""
    expected = child.parent  # parent that we expect
    possible = possible_sibling.parent
    return expected == possible


def read_items(csv: str) -> Iterator[geo.GeoRecord]:
    """Read csv rows into GeoRecords"""
    for row in data.read_csv(csv):
        geo_id, geo_type, *names = row
        cls = geo.GeoMeta.registry[geo_type]
        item = geo.GeoRecord(int(geo_id), cls.from_texts(*names))
        yield item


class Engine:
    def __init__(self, file=None):
        self._trie = trie.Trie()
        # index of added singleton records, handy alias
        self._index = geo.GeoRecord.registry
        self._fixup_counter = 0
        self.lookup = self._trie.lookup

        if file:
            self.index(read_items(file))

    @utils.profile
    def index(self, items: Iterable[geo.GeoRecord]) -> None:
        """Add collection of geo items to the trie"""
        for item in tqdm(items):  # * progressbar eats memory, but helps a lot
            self.add(item)

    @utils.profile
    def export(self, path):
        """Save data from index into csv"""
        data.write_csv(path, collect_data(self._index))
        print(f"Exported to {path}")

    def search(self, name: str, ids: Set[int]) -> List[geo.GeoRecord]:
        """Find id by exact name in subset of ids"""
        records = [self._index.get(i) for i in ids]
        matches = [r for r in records if str(r.item.name) == name]
        return matches

    def add_item(self, item: geo.GeoItem) -> geo.GeoRecord:
        """Convert GeoItem to GeoRecord by creating id and save it"""
        self._fixup_counter -= 1
        record = geo.GeoRecord(id=self._fixup_counter, item=item)
        return self._trie.add(record)

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

            # * lookup by main lang, full name
            query = str(parent.name)
            ids = self._trie.lookup(query, exact=True)
            if ids:
                if len(ids) == 1:
                    # the one parent that we can't choose
                    parent_record = self._index[ids.pop()]
                    if not same_parents(parent, parent_record.item):
                        # but it's grandparent is not ours, let's add correct parent
                        parent_record = self.add_item(parent)

                elif len(ids) > 1:
                    # Ambiguous match, detect correct parent.
                    # Most often word "superset" is matched, because
                    # names are split into many words: "aaa-bbb": "aaa", "bbb"
                    # Search by full name in these ids
                    results = self.search(query, ids)

                    # We may find multiple items with same name, but they may
                    # have different parents. Let's check them
                    checked = [r for r in results if same_parents(parent, r.item)]
                    if checked:
                        if len(checked) > 1:
                            # same parent, same grandparent, bad
                            raise ValueError(f"Duplicate child-parent paths: {checked}")
                        parent_record = checked[0]
                    else:
                        # no parent found, perhaps the archives are incomplete
                        # let's add the expected parent as is
                        parent_record = self.add_item(parent)
            else:
                # Parent is not in index, add it
                parent_record = self.add_item(parent)

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
            items = res.setdefault(obj.item._type, [])
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
            print(self.filter(res, 3))
        print("Bye!")
