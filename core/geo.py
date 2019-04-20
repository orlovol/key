# import re
import regex
import typing

WORD_SEP = ", "
# WORD_RE = r"[\w-]+(?: +[\w-]+)*?"  # words with hyphens and digits
WORD_RE = (
    r"[[:upper:]][\w-]+(?: +[[:upper:]][\w-]+)*?"
)  # words with hyphens and digits # city type fix - first letter uppercase

NAME_RE = fr"(?P<name>{WORD_RE})"
OLDNAME_RE = fr"\(\s*(?P<oldname>{WORD_RE})\s*\)"
FULLNAME_RE = fr"{NAME_RE}\s*(?:{OLDNAME_RE}\s*)?"
FULLNAME = regex.compile(FULLNAME_RE)

RAIONKEY = "район"  # multilingual unique key


class Name(typing.NamedTuple):
    name: str
    old_name: str

    def __str__(self):
        return f"{self.name} ({self.old_name})" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'


def make_name(match):
    return Name(*match.group("name", "oldname"))


class GeoType(typing.NamedTuple):
    geo_id: int
    name: str
    name_uk: str


class GeoMeta(type):
    registry = {}

    def __new__(cls, name, bases, dct):
        """Called for each GeoItem class"""
        geo = super().__new__(cls, name, bases, dct)
        parent = bases[0]  # assume that we subclass one GeoItem at a time, to avoid fold/reduce
        if parent is not GeoType:
            geo._name = name.lower()
            geo.registry = {}  # dictionary of created objects
            cls.registry[geo._name] = geo
        return geo


class GeoItem(GeoType, metaclass=GeoMeta):
    _name: str = None  # class lowercase name - csv key

    def __new__(cls, geo_id, name, name_uk):
        dname = cls.parse(name.split(WORD_SEP))
        dname_uk = cls.parse(name_uk.split(WORD_SEP))

        if cls._name == "address":
            name = dname[cls._name]
            name_uk = dname_uk[cls._name]
        else:
            match = FULLNAME.search(dname[cls._name])
            match_uk = FULLNAME.search(dname_uk[cls._name])
            name = make_name(match)
            name_uk = make_name(match_uk)

        obj = super().__new__(cls, geo_id, name, name_uk)
        if cls._name != "address":
            cls.registry[obj.name.name] = obj
        return obj


class Region(GeoItem):
    @staticmethod
    def parse(words):
        region, *_ = words
        return dict(region=region)


class Raion(GeoItem):
    @staticmethod
    def parse(words):
        *init, raion = words
        sub = Region.parse(init)
        return dict(sub, raion=raion)


class City(GeoItem):
    @staticmethod
    def parse(words):
        *init, city = words

        if len(init) == 1:  # city
            sub = Region.parse(init)
        elif len(init) == 2:  # town
            sub = Raion.parse(init)
        else:
            raise ValueError(f"Problem with city: {words}")

        return dict(sub, city=city)


class District(GeoItem):
    @staticmethod
    def parse(words):
        *init, district = words
        sub = City.parse(init)
        return dict(sub, district=district)


class MicroDistrict(GeoItem):
    @staticmethod
    def parse(words):
        *init, microdistrict = words
        sub = City.parse(init)
        return dict(sub, microdistrict=microdistrict)


class Street(GeoItem):
    @staticmethod
    def parse(words):
        *init, street = words

        if len(init) == 2 or init[1].endswith(RAIONKEY):
            sub = City.parse(init)
        else:
            sub = District.parse(init)

        return dict(sub, street=street)


class Address(GeoItem):
    @staticmethod
    def parse(words):
        *init, address = words
        sub = Street.parse(init)
        return dict(sub, address=address)


TYPES = GeoMeta.registry
