"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


from tqdm import tqdm
from typing import Iterator, Iterable, Set
from functools import partial
from itertools import chain
from collections import defaultdict

from . import utils, geo


def rec_dd():
    return defaultdict(rec_dd)


ITEMSKEY = "_items"


def preprocess(word: str) -> str:
    """Simplify word as much as possible"""
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
    """Сollect items on specified tree node into set"""
    return set(_collect(node))


def _show(node: dict, prefix=""):
    """Recursively simple-print trie structure"""
    print(prefix)
    for key in node.keys():
        if key == ITEMSKEY:
            print(f"{prefix}{ITEMSKEY}: {node[key]}")
        else:
            _show(node[key], prefix + key)


def _analyze(node: dict, info=defaultdict(int)):
    """Recursively collect tree info - key-nodes & item ids"""
    for key in node.keys():
        if key == ITEMSKEY:
            info["item_nodes"] += 1
            info["item_count"] += len(node[key])
        else:
            info["prefix_nodes"] += 1
            _analyze(node[key], info)
    return info


def analyze(node: dict, sizes=False):
    """Gather tree info - key-nodes & item ids, ratio, sizes"""
    info = _analyze(node)
    info["item_mean"] = round(info["item_count"] / info["item_nodes"], 2)
    info["node_ratio"] = round(info["item_nodes"] / info["prefix_nodes"], 2)

    if sizes:  # * note,`utils.total_size` eats memory
        info["size_trie"] = utils.total_size(node)
        info["size_index"] = utils.total_size(list(_collect(node)))
        # ! same as above, without tree traversal, but with magic constant
        info["size_index2"] = utils.sizeof_fmt(10 * info["item_count"])

    return dict(info)


def lookup(node: dict, query: str) -> Iterable[int]:
    """Move down from specified node, following query, and collect items from there"""
    for c in preprocess(query):  # TODO: multiword query
        node = node.get(c)
        if not node:
            return set()
    return collect(node)


def suffixes(word: str) -> Iterator[str]:
    """Return all suffixes of the word"""
    if not word:
        return
    for i, _ in enumerate(word):
        yield word[i:]


class Trie:
    def __init__(self, items=None):
        self.root = rec_dd()
        if items:
            self.index(items)

        self._alphabet = set()
        self._indexed_items = 0

        self.collect = partial(collect, self.root)
        self.lookup = partial(lookup, self.root)

    @property
    def alphabet(self):
        return f'`{"".join(sorted(self._alphabet))}`'

    @property
    def info(self):
        info = analyze(self.root, sizes=True)
        info['alphabet'] = self.alphabet
        info['indexed'] = self._indexed_items
        return info

    @utils.profile
    def index(self, items: Iterable[geo.GeoItem]) -> None:
        """Add collection of geo items to the trie"""
        for item in tqdm(items):  # * progressbar eats memory, but helps a lot
            self.add_item(item)
            self._indexed_items += 1

    def add_item(self, item: geo.GeoItem):
        """Add geo item names to trie
        Add whole word, and all possible suffixes
        """
        for name in (item.name, item.name_uk):  # Name
            # Name is iterable namedtuple: name, old_name, type
            for suffix in chain.from_iterable(map(suffixes, name)):
                self.add_word(item.geo_id, suffix)

    def add_word(self, id_: int, word: str) -> None:
        """Split word into characters and add nested nodes to the trie.
        Append id_ to `items` list in the final node.
        Word may be splitted into subwords, which are added separately"""

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



__all__ = ["Trie"]
