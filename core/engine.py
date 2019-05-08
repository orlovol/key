from difflib import SequenceMatcher
from itertools import combinations, groupby
from pprint import pprint
from typing import Any, Dict, Iterable, List, Set, Tuple

from tqdm import tqdm

from . import data, geo, trie, utils

# latin to cyrillic keyboard layout map
keymap_ru = str.maketrans(
    r"qwertyuiop[]asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхъфывапролджэячсмитьбю."
)
keymap_uk = str.maketrans(
    r"qwertyuiop[]\asdfghjkl;'zxcvbnm,./", r"йцукенгшщзхїґфівапролджєячсмитьбю."
)
KEYMAPS = (keymap_uk, keymap_ru)  # ? language preference can be specified somewhere


def same_parents(child1: geo.GeoItem, child2: geo.GeoItem) -> bool:
    """Check if two items have the same parent. Should have same types and similar names"""
    if child1.type != child2.type:
        return False

    if child1.parent != child2.parent:
        return False

    # okay so types/parents are same, that's good, but children names may not match,
    # they may have similar names, like "anne" and "marianne" but those are different
    # let's compare fullnames, to see if they're really similar
    fullname1, fullname2, oldname = str(child1.name), str(child2.name), child2.name.old_name
    matcher = SequenceMatcher(lambda x: x in "( )", fullname1, fullname2)

    # they are
    if matcher.real_quick_ratio() == 1.0:
        return True

    # if child1 has no old name, maybe its regular name is actually old one
    # let's check if there's oldname in prefix/suffix (because there can be type_name around)
    if (child1.name.old_name is None and oldname is not None) and (
        fullname1.endswith(oldname) or fullname1.startswith(oldname)
    ):
        return True

    return False


def process_id_sets(*word_ids: Set[int], exact: bool) -> Set[int]:
    """Suitable for same-level search words"""
    id_sets = len(word_ids)
    if id_sets == 2 or exact:
        return set.intersection(*word_ids)

    if id_sets > 2:
        # calculate union of paired intersections
        return set().union(*(set.intersection(*pair) for pair in combinations(word_ids, 2)))

    return word_ids[0]

class Engine:
    def __init__(self, file=None):
        self._trie = trie.Trie()
        # index of added singleton records, handy alias
        self._index = geo.GeoRecord.registry
        self._fixup_counter = 0
        self.lookup = self._trie.lookup

        if file:
            self.index(data.read_items(file))


    def lookup_same_level(self, query: str) -> Set[int]:
        exact = True
        word_ids = self._trie.lookup(query, exact)
        return process_id_sets(*word_ids, exact=exact)
    @utils.profile
    def index(self, items: Iterable[geo.GeoRecord]) -> None:
        """Add collection of geo items to the trie"""
        for item in tqdm(items):  # * progressbar eats memory, but helps a lot
            self.add(item)

    @utils.profile
    def export(self, path, as_tree=False):
        """Save data from index into csv"""
        data.write_items(self._index, path, as_tree)
        print(f"Exported {['denormalized', 'tree'][as_tree]} data to {path}")

    def index_match(self, name: str, ids: Set[int]) -> List[geo.GeoRecord]:
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
            ids = self.lookup_same_level(query, exact=True)
            if ids:
                if len(ids) == 1:
                    # the one parent that we can't choose
                    parent_record = self._index[ids.pop()]
                    if not same_parents(parent, parent_record.item):
                        # let's add correct parent
                        parent_record = self.add_item(parent)

                elif len(ids) > 1:
                    # Ambiguous match, detect correct parent.
                    # Most often word "superset" is matched, because
                    # names are split into many words: "aaa-bbb": "aaa", "bbb"
                    # Search by full name in these ids
                    results = self.index_match(query, ids)

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

    def filter(self, results: Set[int], query: str, as_dict=True, maxcount=3) -> Dict:
        """Filter & format search results"""
        items: List[Any] = []
        hidden = count = len(results)
        for r in results:
            record = self._index[r]
            if len(items) < maxcount:
                item = record.as_dict(query) if as_dict else record
                items.append(item)
                hidden -= 1
        return {"results": items, "query": query, "hidden": hidden, "count": count}

    def wrong_layout(self, query: str) -> Tuple[str, Set[int]]:
        """Search same query in other keyboard layouts.
        Return translated query and results"""
        for m in KEYMAPS:
            translated = query.translate(m)
            ids = self.lookup(translated)
            if ids:
                return (translated, ids)
        return (query, set())

    def search(self, query):
        """Perform search and return results"""
        ids = self.lookup(query)
        if not ids:
            query, ids = self.wrong_layout(query)
        return self.filter(ids, query=query, as_dict=True, maxcount=20)

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

            ids = self.lookup(query)
            if not ids:
                query, ids = self.wrong_layout(query)
                ids and print(f"Did you mean _{query}_?")
            print(self.filter(ids, query, 3))
        print("Bye!")
