import re
from typing import NamedTuple, Iterable
from collections import OrderedDict

WORD_SEP = ", "
RAIONKEY = "район"  # multilingual unique key for raion/district

OLD_NAME_RE = fr"\s*\(\s*(?P<old_name>.*)\s*\)"
OLD_NAME = re.compile(OLD_NAME_RE)


class Name(NamedTuple):
    name: str
    old_name: str

    def __str__(self):
        return f"{self.name} ~{self.old_name}" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'


class Names(NamedTuple):
    name: Name
    name_uk: Name


def words_to_names(words: Iterable[str]) -> Names:
    old_name = None

    def repl(match):
        nonlocal old_name
        old_name = match.group("old_name")
        return ""

    names = []
    for word in words:
        old_name = None
        name = Name(name=OLD_NAME.sub(repl, word, 1), old_name=old_name)
        names.append(name)
    return Names(*names)


class GeoMeta(type):
    _registry = {}

    def __new__(cls, name, bases, dct):
        """Called for each GeoItem class"""
        geo = super().__new__(cls, name, bases, dct)
        parent = bases[0]  # assume that we subclass one GeoItem at a time, to avoid fold/reduce
        if parent is not Names:
            geo._name = name.lower()
            cls._registry[geo._name] = geo  # add geotype registry to meta
        return geo


class GeoName(Names, metaclass=GeoMeta):
    """Simple class that contains name and type, without id"""

    def __new__(cls, names: Iterable[str], parent=None):
        obj = super().__new__(cls, *names)  # most often it's Names
        obj.parent = parent
        return obj

    @classmethod
    def from_text(cls, text):
        # tuples of words in all languages for each level
        level_words = zip(*(word.split(WORD_SEP) for word in text))
        level_names = map(words_to_names, level_words)
        return cls.parse(level_names)


class GeoItem(NamedTuple):
    id: int
    name: GeoName


class Region(GeoName):
    order = 10

    @classmethod
    def parse(cls, names: Iterable[Name]):
        region, *_ = names
        return cls(region)


class Raion(GeoName):
    order = 20

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, raion = names
        parent = Region.parse(init)
        return cls(raion, parent)


class City(GeoName):
    order = 30

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, city = names

        if len(init) == 1:  # region.city
            parent = Region.parse(init)
        elif len(init) == 2:  # region.raion.city (town)
            parent = Raion.parse(init)
        else:
            raise ValueError(f"Problem with City: {names}")

        return cls(city, parent)


class District(GeoName):
    order = 40

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, district = names
        parent = City.parse(init)
        return cls(district, parent)


class MicroDistrict(GeoName):
    order = 50

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, microdistrict = names
        parent = City.parse(init)
        return cls(microdistrict, parent)


class Street(GeoName):
    order = 60

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, street = names

        if len(init) == 2 or init[1].endswith(RAIONKEY):
            parent = City.parse(init)
        else:
            parent = District.parse(init)

        return cls(street, parent)


class Address(GeoName):
    order = 70

    @classmethod
    def parse(cls, names: Iterable[Name]):
        *init, address = names
        parent = Street.parse(init)
        return cls(address, parent)


# * py3.7 keeps dict insertion order, but use OrderedDict+order TO:
# * secure against order of GeoName declarations
# * secure against older python versions
# * allow specific ordering
TYPES = OrderedDict(sorted(GeoMeta._registry.items(), key=lambda p: p[1].order))
ORDERS = {v._name: v.order for v in GeoMeta._registry.values()}
