import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import ClassVar, Dict, Iterable, Iterator, NamedTuple, Optional, Tuple

WORD_SEP = ", "
RAIONKEY = "район"  # bilingual unique key for raion/district

OLD_NAME_RE = fr"\s*\(\s*(?P<old_name>.*)\s*\)"
OLD_NAME = re.compile(OLD_NAME_RE)


class Name(NamedTuple):
    """Name definition for item"""

    name: str
    old_name: Optional[str]

    def __str__(self):
        return f"{self.name} ~{self.old_name}" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'


def words_to_names(lang_words: Tuple[str, ...]) -> Iterator[Name]:
    """Convert tuples of name strings into Name items and wrap into LangNames"""
    old_name = None

    def repl(match):
        nonlocal old_name
        old_name = match.group("old_name")
        return ""

    for lang in lang_words:
        old_name = None
        name = Name(name=OLD_NAME.sub(repl, lang, 1), old_name=old_name)
        yield name


# Multilingual Name collection
LangNames = Tuple[Name, ...]


def to_names(words: Tuple[str, ...]) -> LangNames:
    return tuple(words_to_names(words))


class GeoMeta(type):
    _registry: Dict[str, "GeoItem"] = {}

    def __new__(cls, name, bases, dct):
        """Called for each GeoRecord class"""
        geo = super().__new__(cls, name, bases, dct)
        if bases:
            geo._name = name.lower()
            cls._registry[geo._name] = geo  # add geotype registry to meta
        return geo


class GeoItem(metaclass=GeoMeta):
    """Simple class that contains name and type, without id"""

    order = 0
    _name = None

    __slots__ = ["name", "name_uk", "parent"]

    def __init__(self, names: LangNames, parent: Optional["GeoItem"] = None):
        self.name, self.name_uk, *_ = names
        self.parent: Optional["GeoItem"] = parent

    def __iter__(self):
        """Iterate over Names"""
        yield self.name
        yield self.name_uk

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    @classmethod
    def from_texts(cls, *texts: str):
        # tuples of words in all languages for each level
        level_words: Iterable[Tuple[str, ...]] = zip(*(word.split(WORD_SEP) for word in texts))
        level_names: Iterable[LangNames] = map(to_names, level_words)
        return cls.parse(*level_names)

    @classmethod
    def parse(cls, *names: LangNames):
        raise NotImplementedError("GeoItem is abstract")


@dataclass(frozen=True)
class GeoRecord:
    """Container for GeoItem with id"""

    id: int
    item: GeoItem
    registry: ClassVar[Dict[int, "GeoRecord"]] = {}

    def __new__(cls, id, item):
        try:
            obj = cls.registry[id]

        except KeyError:
            obj = object.__new__(cls)
            cls.registry[id] = obj

        else:
            if (obj.id == id) != (obj.item == item):
                raise ValueError(f"Collision with existing {obj}: ({id}, {item})")

        return obj


class Region(GeoItem):
    order = 10

    @classmethod
    def parse(cls, *names: LangNames):
        region, *_ = names
        return cls(region)


class Raion(GeoItem):
    order = 20

    @classmethod
    def parse(cls, *names: LangNames):
        *init, raion = names
        parent = Region.parse(*init)
        return cls(raion, parent)


class City(GeoItem):
    order = 30

    @classmethod
    def parse(cls, *names: LangNames):
        *init, city = names

        if len(init) == 1:  # region.city
            parent = Region.parse(*init)
        elif len(init) == 2:  # region.raion.city (town)
            parent = Raion.parse(*init)
        else:
            raise ValueError(f"Problem with City: {names}")

        return cls(city, parent)


class District(GeoItem):
    order = 40

    @classmethod
    def parse(cls, *names: LangNames):
        *init, district = names
        parent = City.parse(*init)
        return cls(district, parent)


class MicroDistrict(GeoItem):
    order = 50

    @classmethod
    def parse(cls, *names: LangNames):
        *init, microdistrict = names
        parent = City.parse(*init)
        return cls(microdistrict, parent)


class Street(GeoItem):
    order = 60

    @classmethod
    def parse(cls, *names: LangNames):
        *init, street = names

        # second item of init
        # its first language name
        # its regular name
        # it's probably raion
        maybe_raion = init[1][0].name.endswith(RAIONKEY)

        if len(init) == 2 or maybe_raion:
            parent = City.parse(*init)
        else:
            parent = District.parse(*init)

        return cls(street, parent)


class Address(GeoItem):
    order = 70

    @classmethod
    def parse(cls, *names: LangNames):
        *init, address = names
        parent = Street.parse(*init)
        return cls(address, parent)


# * py3.7 keeps dict insertion order, but use OrderedDict+order TO:
# * secure against order of GeoItem declarations
# * secure against older python versions
# * allow specific ordering
TYPES = OrderedDict(sorted(GeoMeta._registry.items(), key=lambda p: p[1].order))
ORDERS = {v._name: v.order for v in GeoMeta._registry.values()}
