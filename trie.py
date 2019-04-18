"""
Trie implementation for prefix search

Expects values in form of (int key, string value)
Keys should be unique, values - any alphanumeric sequences
"""


from tqdm import tqdm
from typing import Iterable, Tuple, Set
from itertools import chain
from collections import defaultdict

from utils import total_size

try:
    profile()
except NameError:
    profile = lambda x: x  # noqa


def rec_dd():
    return defaultdict(rec_dd)


TRIE = rec_dd()
ITEMSKEY = "_items"


def add(id_: int, word: str) -> None:
    """Split word into characters and add to the tree.
       Insert id into `items` list after last character.
    """
    level = TRIE
    for c in word.lower():  # ? more preprocessing?
        level = level[c]

    # we can't have two different words with same tree-path
    # but they can have multiple ids, so let's expect that and save to list
    items = level.setdefault(ITEMSKEY, list())
    if id_ not in items:
        items.append(id_)


def collect(level: dict) -> Iterable[int]:
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
            print(f"{ITEMSKEY}: {level[key]}")
        else:
            show(level[key], prefix + key)


@profile
def index(items: Iterable[Tuple[int, str]]) -> Set[int]:
    """Add items to index and return set of present ids"""
    for item in tqdm(items):  # * progressbar eats memory, but helps a lot
        add(*item)

    # * collect returns duplicated ids, but we may use `set` to return unique ids
    # * and present them in preferred language
    added = set(collect(TRIE))  # same as input ids
    return added


@profile
def _words():

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

    words_ += [(a[::-1], b[::-1]) for a, b in words_]  # add more fake words

    alphabet = "".join(sorted(set(c for pair in words_ for c in "".join(pair).lower())))

    id_mul = 1000  # * same words, more ids
    word_mul = 20  # * more words, same ids

    word_len = 2 * len(words_)
    id_len = word_len * id_mul

    print(
        f"""\
Alphabet: `{alphabet}` ({len(alphabet)})
Unique words: {word_len}
IDs: {id_len}
Total words: {id_len * word_mul}
"""
    )

    # unpack language pairs with same id, multiply words/ids
    words = [(i, word) for i, pair in enumerate(words_ * id_mul) for word in pair] * word_mul
    return words


if __name__ == "__main__":
    import timing  # noqa

    words = _words()
    added = index(words)

    assert added == set(i for i, _ in words)

    len_added, len_input = len(added), len(words)

    info = analyze(TRIE)
    # show(TRIE)

    # `total_size` eats memory too
    print(
        f"""
Input words: {len_input}
Added ids: {len_added} ({len_added / len_input:.2%})
Tree Size: {total_size(TRIE)}
Index Size: {total_size(added)}
Info: {dict(info)}
    """
    )
