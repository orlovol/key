"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


from tqdm import tqdm
from typing import Iterator, Iterable, Tuple, Set
from functools import partial
from itertools import chain
from collections import defaultdict

from . import utils

try:
    profile()
except NameError:
    profile = lambda x: x  # noqa


def rec_dd():
    return defaultdict(rec_dd)


ITEMSKEY = "_items"


def _collect(node: dict) -> Iterable[int]:
    """Recursively collect items on specified tree node"""
    keys = set(node.keys()) - {ITEMSKEY}
    return chain(node.get(ITEMSKEY, []), *(_collect(node[key]) for key in keys))


def collect(node: dict) -> Set[int]:
    """Сollect items on specified tree node into set"""
    return set(_collect(node))


def _show(node, prefix=""):
    """Recursively simple-print trie structure"""
    print(prefix)
    for key in node.keys():
        if key == ITEMSKEY:
            print(f"{prefix}{ITEMSKEY}: {node[key]}")
        else:
            _show(node[key], prefix + key)


def _analyze(node, info=defaultdict(int)):
    """Recursively collect tree info - key-nodes & item ids"""
    for key in node.keys():
        if key == ITEMSKEY:
            info["ids"] += len(node[key])
        else:
            info["nodes"] += 1
            _analyze(node[key], info)
    return info


def analyze(node, sizes=False):
    """Collect tree info - key-nodes & item ids, ratio, size"""
    info = _analyze(node)
    info["ratio"] = round(info["ids"] / info["nodes"], 2)

    if sizes:  # `utils.total_size` eats memory
        info["trie_size"] = utils.total_size(node)
        info["index_size"] = utils.total_size(list(_collect(node)))
        # ! same as above, without tree traversal, but with magic constant
        info["index_size2"] = utils.sizeof_fmt(10 * info["ids"])

    return dict(info)


def lookup(node: dict, query: str) -> Iterable[int]:
    """Move down from specified node, following query, and collect items from there"""
    for c in query.lower():
        node = node.get(c)
        if not node:
            return set()
    return collect(node)


def suffixes(word: str) -> Iterator[str]:
    """Return all suffixes of the word"""
    for i, _ in enumerate(word):
        yield word[i:]


class Trie:
    def __init__(self, items=None):
        self.root = rec_dd()
        if items:
            self.index(items)

        self.analyze = partial(analyze, self.root)
        self.collect = partial(collect, self.root)
        self.lookup = partial(lookup, self.root)

    @profile
    def index(self, items: Iterable[Tuple[int, str]]) -> Set[int]:
        """Add items to the trie"""
        for id_, word in tqdm(items):  # * progressbar eats memory, but helps a lot
            word, *_ = word.partition(" ")  # ! TODO: don't index `type`
            for suffix in suffixes(word):
                self.add(id_, suffix)

    def add(self, id_: int, word: str) -> None:
        """Split word into characters and add nested nodes to the trie.
        Append id_ to `items` list in the final node."""

        node = self.root
        for c in word.lower():  # ? more preprocessing?
            node = node[c]

        # we can't have two different words with same tree-path
        # but they can have multiple ids, so let's keep them in a list
        items = node.setdefault(ITEMSKEY, list())
        if id_ not in items:
            items.append(id_)


@profile
def _make_items():
    """Test method to create some items"""

    words_ = [
        ("Винницкая область", "Вінницька область"),
        ("Волынская область", "Волинська область"),
        ("Днепропетровская область", "Дніпропетровська область"),
        ("Донецкая область", "Донецька область"),
        ("Житомирская область", "Житомирська область"),
        ("Закарпатская область", "Закарпатська область"),
        ("Запорожская область", "Запорізька область"),
        ("Ивано-Франковская область", "Івано-Франківська область"),
        ("Киевская область", "Київська область"),
        ("Кировоградская область", "Кіровоградська область"),
        ("Крым", "Крим"),
        ("Луганская область", "Луганська область"),
        ("Львовская область", "Львівська область"),
        ("Николаевская область", "Миколаївська область"),
        ("Одесская область", "Одеська область"),
        ("Полтавская область", "Полтавська область"),
        ("Ровенская область", "Рівненська область"),
        ("Сумская область", "Сумська область"),
        ("Тернопольская область", "Тернопільська область"),
        ("Харьковская область", "Харківська область"),
        ("Херсонская область", "Херсонська область"),
        ("Хмельницкая область", "Хмельницька область"),
        ("Черкасская область", "Черкаська область"),
        ("Черниговская область", "Чернігівська область"),
        ("Черновицкая область", "Чернівецька область"),
    ]

    id_mul = 1  # * same words, more ids
    word_mul = 1  # * more words, same ids

    # unpack language pairs with same id, multiply words/ids
    words = [(i, word) for i, pair in enumerate(words_ * id_mul) for word in pair] * word_mul
    return words


def _repl(lookup, items):
    query = "Enter query (empty to exit):"
    print(query)
    while query:
        query = input("> ")
        if query:
            res = lookup(query)
            print([items[r] for r in res])
    print("Bye!")


if __name__ == "__main__":
    import sys

    interactive = len(sys.argv) > 1

    if not interactive:
        from . import timing  # noqa

    items = _make_items()

    trie = Trie(items)
    added = trie.collect()

    len_items, len_added = len(items), len(added)

    info = "\n".join(f"{key.title()}: {value}" for key, value in trie.analyze(sizes=True).items())

    print(
        f"""\
Input words: {len_items}
Added ids: {len_added} ({len_added / len_items:.2%})
{info}
    """
    )

    # _show(trie.root)
    if interactive:
        _repl(trie.lookup, dict(items))  # dict removes duplicated ids (multiple languages)


__all__ = ["Trie"]
