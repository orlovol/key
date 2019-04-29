import re

from dataclasses import dataclass
from typing import ClassVar, Dict, Iterable, Iterator, List, NamedTuple, Optional, Tuple

RAIONKEY = "район"  # bilingual unique key for raion/district
WORD_SEP = re.compile(r", (?![^(]*\))")
OLD_NAME = re.compile(r"\s*\(\s*(?P<old_name>.*?)\s*\)\s*")
SPACES = re.compile(" {2,}")


class Name(NamedTuple):
    """Name definition for item"""

    name: str
    old_name: Optional[str]

    def __str__(self):
        return f"{self.name} ({self.old_name})" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'


# Multilingual Name collection
LangNames = Tuple[Name, ...]


def _words_to_names(lang_words: Iterable[str]) -> Iterator[Name]:
    """Convert tuples of name strings into Name items and wrap into LangNames"""
    old_name = None

    def repl(match):
        nonlocal old_name
        old_name = match.group("old_name")
        return " "

    for lang in lang_words:
        old_name = None
        name = OLD_NAME.sub(repl, lang, 1).strip()
        yield Name(name, old_name)


def to_names(words: Iterable[str]) -> LangNames:
    return tuple(_words_to_names(words))


class GeoMeta(type):
    registry: Dict[str, "GeoItem"] = {}

    def __new__(cls, name, bases, dct):
        """Called for each class with this metaclass"""
        geo = super().__new__(cls, name, bases, dct)
        if bases:  # then it's GeoItem
            geo.type = name.lower()
            cls.registry[geo.type] = geo  # add geotype registry to meta
        return geo


class GeoItem(metaclass=GeoMeta):
    """Simple class that contains name and type, without id"""

    __slots__ = ["name", "name_uk", "parent"]
    type = None

    def __init__(self, names: LangNames, parent: Optional["GeoItem"] = None):
        self.name, self.name_uk, *_ = names
        self.parent: Optional["GeoItem"] = parent

    def __iter__(self):
        """Iterate over languages/Names"""
        yield self.name
        yield self.name_uk

    def __eq__(self, other):
        if isinstance(other, GeoRecord):
            other = other.item
        if isinstance(other, GeoItem):
            return list(self) == list(other) and self.parent == other.parent
        return NotImplemented

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    @classmethod
    def from_texts(cls, *texts: str):
        # (words of one lang) for each language
        langs: Iterator[List[str]] = (WORD_SEP.split(SPACES.sub(" ", lang)) for lang in texts)
        # (level words in one language) for each level
        level_words: Iterable[Tuple[str, ...]] = zip(*langs)
        # (names) for each level
        level_names: Iterable[LangNames] = map(to_names, level_words)
        return cls.parse(*level_names)

    @classmethod
    def parse(cls, *names: LangNames):
        raise NotImplementedError("GeoItem is abstract")

    @property
    def item(self):
        """Alias to simplify code when working with mixed GeoRecord/GeoItem content"""
        return self


@dataclass(frozen=True)
class GeoRecord:
    """Container for GeoItem with id"""

    __slots__ = ["id", "item"]
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

    def __eq__(self, other):
        if isinstance(other, GeoRecord):
            return (self.id, self.item) == (other.id, other.item)
        return NotImplemented


class Region(GeoItem):
    @classmethod
    def parse(cls, *names: LangNames):
        region, *_ = names
        return cls(region)


class Raion(GeoItem):
    @classmethod
    def parse(cls, *names: LangNames):
        *init, raion = names
        parent = Region.parse(*init)
        return cls(raion, parent)


class City(GeoItem):
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
    @classmethod
    def parse(cls, *names: LangNames):
        *init, district = names
        parent = City.parse(*init)
        return cls(district, parent)


class MicroDistrict(GeoItem):
    @classmethod
    def parse(cls, *names: LangNames):
        *init, microdistrict = names
        parent = City.parse(*init)
        return cls(microdistrict, parent)


class Street(GeoItem):
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
    @classmethod
    def parse(cls, *names: LangNames):
        *init, address = names
        parent = Street.parse(*init)
        return cls(address, parent)
