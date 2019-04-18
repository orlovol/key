"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


import sys
from typing import Iterable, Tuple
from itertools import chain
from collections import defaultdict

from memory_profiler import profile


def rec_dd():
    return defaultdict(rec_dd)


TRIE = rec_dd()
ITEMSKEY = "_items"


def add(id_, word):
    """Split word into characters and add to the tree.
       Insert id into `items` list after last character.
    """
    level = TRIE
    for c in word:
        level = level[c]
    # we can't have two different words with same tree-path
    # but they can have multiple ids, so let's expect that
    items = level.setdefault(ITEMSKEY, list())
    if id_ not in items:
        items.append(id_)


def collect(level) -> Iterable[int]:
    """Collect items on specified tree level
    """
    keys = set(level.keys()) - {ITEMSKEY}
    return chain(level.get(ITEMSKEY, []), *(collect(level[key]) for key in keys))


def analyze(level, info=defaultdict(int)):
    """Collect tree info - number of levels, key-nodes, item ids
    """
    info["levels"] += 1
    for key in level.keys():
        info["nodes"] += 1
        if key == ITEMSKEY:
            info["ids"] += len(level[key])
        else:
            analyze(level[key], info)
    return info


def show(level, prefix=""):
    print(prefix)
    for key in level.keys():
        if key == ITEMSKEY:
            print(level[key])
        else:
            show(level[key], prefix + key)


@profile
def main(items: Iterable[Tuple[int, str]]):
    l = len(items)
    k = l/10
    for i, item in enumerate(items):
        if not (i % k):
            print(f"{i/l:.0%}")
        add(*item)
    print()

    items = sorted(collect(TRIE))

    # show(TRIE)
    info = analyze(TRIE)

    li, lw = len(items), len(words)
    print(
        f"""\
Input ids: {lw}
Added ids: {li} ({li / lw:.2%})
Tree Size: {sys.getsizeof(TRIE) / 1024:.2f} KB
Index Size: {sys.getsizeof(items) / 1024:.2f} KB
Info: {dict(info)}\
    """
    )


if __name__ == "__main__":
    import timing  # local helper

    words_ = [
        ("Запорожская область", "Запорізька область"),
        ("Киевская область", "Київська область"),
        ("Хмельницкая область", "Хмельницька область"),
        ("Закарпатская область", "Закарпатська область"),
        ("Ровенская область", "Рівненська область"),
        ("Черниговская область", "Чернігівська область"),
        ("Кировоградская область", "Кіровоградська область"),
        ("Херсонская область", "Херсонська область"),
        ("Черкасская область", "Черкаська область"),
        ("Житомирская область", "Житомирська область"),
        ("Одесская область", "Одеська область"),
        ("Львовская область", "Львівська область"),
        ("Харьковская область", "Харківська область"),
        ("Волынская область", "Волинська область"),
        ("Полтавская область", "Полтавська область"),
        ("Николаевская область", "Миколаївська область"),
        ("Тернопольская область", "Тернопільська область"),
        ("Днепропетровская область", "Дніпропетровська область"),
        ("Крым", "Крим"),
        ("Черновицкая область", "Чернівецька область"),
        ("Луганская область", "Луганська область"),
        ("Донецкая область", "Донецька область"),
        ("Сумская область", "Сумська область"),
        ("Ивано-Франковская область", "Івано-Франківська область"),
        ("Винницкая область", "Вінницька область"),
    ]

    words_ = [(a.lower(), b.lower()) for (a, b) in words_]

    alphabet = "".join(sorted(set(chain(*chain(*words_)))))
    print(f"Alphabet ({len(alphabet)}): {alphabet}")

    word_len = 2 * len(words_)
    id_mul = 2  # same words, more ids
    word_mul = 2000  # more words, same ids

    words = (
        list(chain.from_iterable((((i, a), (i, b)) for i, (a, b) in enumerate(words_ * id_mul))))
        * word_mul
    )
    main(words)
    print(f"Params: {word_len} unique/{word_len*word_mul*id_mul} words, {word_len*id_mul} ids")
