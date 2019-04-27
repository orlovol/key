"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


from collections import defaultdict
from functools import partial
from itertools import chain, combinations
from typing import Iterable, Iterator, Set

from . import geo, utils

ITEMSKEY = "_items"
SUFFIXKEY = "_suffix"
KEYS = {ITEMSKEY, SUFFIXKEY}


def preprocess(word: str) -> str:
    """Simplify word as much as possible"""
    replacements = [("'", ""), ("ё", "е")]  # ? bad idea, but ё is so rarely used
    for p in replacements:
        word = word.replace(*p)
    return word.lower()


def preprocess_words(word: str) -> Iterable[str]:
    """Simplify word as much as possible"""
    if not word:
        return []
    word = word.replace("-", " ")
    return (preprocess(w) for w in word.split())


def _collect(node: dict, exact: bool) -> Iterable[int]:
    """Recursively collect items on specified tree node"""
    keys = set(node.keys()) - KEYS  # only prefix nodes
    suffixes = [] if exact else node.get(SUFFIXKEY, [])
    return chain(suffixes, node.get(ITEMSKEY, []), *(_collect(node[key], exact) for key in keys))


def collect(node: dict, exact: bool) -> Set[int]:
    """Collect items on specified tree node into set"""
    return set(_collect(node, exact))


def _show(node: dict, prefix=""):
    """Recursively simple-print trie structure"""
    print(prefix)
    for key in node.keys():
        if key in {ITEMSKEY, SUFFIXKEY}:
            print(f"{prefix}{key}: {node[key]}")
        else:
            _show(node[key], prefix + key)


def _analyze(node: dict, depth=0, info=defaultdict(int)):
    """Helper that recursively collects tree info - node counts"""
    info["depth"] = max(info["depth"], depth)
    for key in node.keys():
        if key == ITEMSKEY:
            info["georecord_containers"] += 1
            info["georecord_items"] += len(node[key])
        elif key == SUFFIXKEY:
            info["suffix_containers"] += 1
            info["suffix_items"] += len(node[key])
        else:
            info["prefix_nodes"] += 1
            _analyze(node[key], depth + 1, info)
    return info


def analyze(node: dict, sizes=False):
    """Gather tree info - key-nodes & item ids, ratio, sizes"""
    import math

    info = _analyze(node, 0)
    if info["depth"]:
        info["branching"] = round(math.log(info["prefix_nodes"], info["depth"]), 2)

        info["georecord_density"] = round(info["georecord_items"] / info["georecord_containers"], 2)
        info["suffix_density"] = round(info["suffix_items"] / info["suffix_containers"], 2)

        info["ratio_geo_pfx"] = round(info["georecord_containers"] / info["prefix_nodes"], 2)
        info["ratio_sfx_pfx"] = round(info["suffix_containers"] / info["prefix_nodes"], 2)

        info["ratio_sfx_geo_containers"] = round(
            info["suffix_containers"] / info["georecord_containers"], 2
        )
        info["ratio_sfx_geo_items"] = round(info["suffix_items"] / info["georecord_items"], 2)

        info["itemkeys_containers"] = info["suffix_containers"] + info["georecord_containers"]
        info["itemkeys_items"] = info["suffix_items"] + info["georecord_items"]
        info["itemkeys_density"] = round(info["itemkeys_items"] / info["itemkeys_containers"], 2)

        if sizes:  # * note,`utils.total_size` eats memory
            info["size_trie"] = utils.total_size(node)
            info["size_itemkeys"] = utils.total_size(list(_collect(node, exact=False)))
            # ! same as above, without tree traversal, but with magic constant
            info["size_itemkeys2"] = utils.sizeof_fmt(10 * (info["itemkeys_items"]))

    return dict(info)


def lookup(root: dict, query: str, exact: bool = False) -> Set[int]:
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
            word_ids.append(collect(node, exact))

    id_sets = len(word_ids)
    if id_sets == 2 or exact:
        return set.intersection(*word_ids)

    if id_sets > 2:
        # calculate union of paired intersections
        return set.union(*(set.intersection(*pair) for pair in combinations(word_ids, 2)))

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

    def _add_word(self, id_: int, word: str, key: str) -> None:
        """Split word into characters and add nested nodes to the trie.
        Append id_ to `items` list in the final node.
        Word may be splitted into subwords, which are added separately
        """
        node = self.root
        for c in word:
            self._alphabet.add(c)
            node = node[c]
        # we can't have two different words with same tree-path
        # but they can have multiple ids, so let's keep them in a list
        items = node.setdefault(key, list())
        if id_ not in items:
            items.append(id_)

    def add(self, record: geo.GeoRecord):
        """Add geo names to trie in multiple languages
        Add whole word, and all its suffixes
        """
        # ! TODO: chain
        # Name objects for different languages
        for lang_name in record.item:
            # Name is iterable namedtuple: name, old_name
            for name in lang_name:
                # split into words
                for word in preprocess_words(name):
                    # retrieve suffixes
                    for i, suffix in enumerate(suffixes(word)):
                        key = SUFFIXKEY if i else ITEMSKEY
                        self._add_word(record.id, suffix, key)

        self._indexed_items += 1
        return True


__all__ = ["Trie"]
