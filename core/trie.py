"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


from typing import Iterator, Iterable, Set
from functools import partial
from itertools import chain, combinations
from collections import defaultdict

from . import utils, geo


ITEMSKEY = "_items"


def preprocess(word: str) -> str:
    """Simplify word as much as possible"""
    replacements = [
        ("'", ""),
        ("ё", "е")  # ? bad idea, but it's so rarely used
    ]
    for p in replacements:
        word = word.replace(*p)
    return word.lower()


def preprocess_words(word: str) -> Iterable[str]:
    """Simplify word as much as possible"""
    word = word.replace("-", " ")
    return (preprocess(w) for w in word.split())


def _collect(node: dict) -> Iterable[int]:
    """Recursively collect items on specified tree node"""
    keys = set(node.keys()) - {ITEMSKEY}
    return chain(node.get(ITEMSKEY, []), *(_collect(node[key]) for key in keys))


def collect(node: dict) -> Set[int]:
    """Collect items on specified tree node into set"""
    return set(_collect(node))


def _show(node: dict, prefix=""):
    """Recursively simple-print trie structure"""
    print(prefix)
    for key in node.keys():
        if key == ITEMSKEY:
            print(f"{prefix}{ITEMSKEY}: {node[key]}")
        else:
            _show(node[key], prefix + key)


def _analyze(node: dict, depth=0, info=defaultdict(int)):
    """Helper that recursively collects tree info - node counts"""
    info["depth"] = max(info["depth"], depth)
    for key in node.keys():
        if key == ITEMSKEY:
            info["item_nodes"] += 1
            info["item_count"] += len(node[key])
        else:
            info["prefix_nodes"] += 1
            _analyze(node[key], depth + 1, info)
    return info


def analyze(node: dict, sizes=False):
    """Gather tree info - key-nodes & item ids, ratio, sizes"""
    info = _analyze(node, 0)
    info["item_mean"] = round(info["item_count"] / info["item_nodes"], 2)
    info["node_type_ratio"] = round(info["item_nodes"] / info["prefix_nodes"], 2)

    if sizes:  # * note,`utils.total_size` eats memory
        info["size_trie"] = utils.total_size(node)
        info["size_index"] = utils.total_size(list(_collect(node)))
        # ! same as above, without tree traversal, but with magic constant
        info["size_index2"] = utils.sizeof_fmt(10 * info["item_count"])

    return dict(info)


def lookup(root: dict, query: str) -> Set[int]:
    """Move down from specified root node, following query, and collect items from there"""
    if not query:
        return set()

    word_ids = []  # list of sets of ids of items that correspond to query
    for word in preprocess_words(query):
        node = root
        for c in word:
            node = node.get(c)
            if not node:
                # dead-end for this word
                word_ids.append(set())
                break
        else:
            word_ids.append(collect(node))

    id_sets = len(word_ids)
    if id_sets > 2:
        # calculate union of paired intersections
        return set.union(*(set.intersection(*pair) for pair in combinations(word_ids, 2)))

    if id_sets == 2:
        return set.intersection(*word_ids)

    return word_ids[0]


def suffixes(word: str) -> Iterator[str]:
    """Return all suffixes of the word"""
    if not word:
        return
    for i, _ in enumerate(word):
        yield word[i:]


class Trie:
    def __init__(self, items=None):
        self.root = utils.rec_dd()
        self._alphabet = set()
        self._indexed_items = 0

        # methods
        self.collect = partial(collect, self.root)
        self.lookup = partial(lookup, self.root)
        self.show = partial(_show, self.root)

        if items:
            self.index(items)

    @property
    def alphabet(self):
        return f'`{"".join(sorted(self._alphabet))}`'

    @property
    def info(self):
        info = analyze(self.root, sizes=True)
        info["alphabet"] = self.alphabet
        info["indexed"] = self._indexed_items
        return info

    def _add_word(self, id_: int, word: str) -> None:
        """Split word into characters and add nested nodes to the trie.
        Append id_ to `items` list in the final node.
        Word may be splitted into subwords, which are added separately
        """
        for subword in preprocess_words(word):
            node = self.root
            for c in subword:
                self._alphabet.add(c)
                node = node[c]
            # we can't have two different words with same tree-path
            # but they can have multiple ids, so let's keep them in a list
            items = node.setdefault(ITEMSKEY, list())
            if id_ not in items:
                items.append(id_)

    def add(self, item: geo.GeoItem):
        """Add geo item names to trie
        Add whole word, and all its suffixes
        """
        for name in (item.name, item.name_uk):  # Name
            # Name is iterable namedtuple: name, old_name
            for suffix in chain.from_iterable(map(suffixes, name)):
                self._add_word(item.geo_id, suffix)

        self._indexed_items += 1
        return True


__all__ = ["Trie"]
