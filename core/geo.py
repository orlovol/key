import re
import typing

WORD_SEP = ", "
RAIONKEY = "район"  # multilingual unique key for raion/district

OLDNAME_RE = fr"\s*\(\s*(?P<oldname>.*)\s*\)"
OLDNAME = re.compile(fr"\s*\(\s*(?P<oldname>.*)\s*\)")


class Name(typing.NamedTuple):
    name: str
    old_name: str

    def __str__(self):
        return f"{self.name} #{self.old_name}" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'


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
            geo.registry = {}  # add registry of created geo-objects to geotype
            cls.registry[geo._name] = geo  # add geotype registry to meta
        return geo


class GeoItem(GeoType, metaclass=GeoMeta):
    _name: str = None  # class lowercase name - csv key

    def __new__(cls, geo_id, name, name_uk):
        name = cls.get_name(name)
        name_uk = cls.get_name(name_uk)
        obj = super().__new__(cls, geo_id, name, name_uk)

        if cls != Address:
            cls.registry[obj.name.name] = obj

        return obj

    @classmethod
    def get_name(cls, string):
        dname = cls.parse(string.split(WORD_SEP))
        word = dname[cls._name]
        oldname = None

        def repl(match):
            nonlocal oldname
            oldname = match.group("oldname")
            return ""

        name = OLDNAME.sub(repl, word, 1)
        name_obj = Name(name, oldname)
        return name_obj


class Region(GeoItem):
    order = 10

    @classmethod
    def parse(cls, words):
        region, *_ = words
        return dict(region=region)


class Raion(GeoItem):
    order = 20

    @classmethod
    def parse(cls, words):
        *init, raion = words
        sub = Region.parse(init)
        return dict(sub, raion=raion)


class City(GeoItem):
    order = 30

    @classmethod
    def parse(cls, words):
        *init, city = words

        if len(init) == 1:  # city
            sub = Region.parse(init)
        elif len(init) == 2:  # town
            sub = Raion.parse(init)
        else:
            raise ValueError(f"Problem with city: {words}")

        return dict(sub, city=city)


class District(GeoItem):
    order = 40

    @classmethod
    def parse(cls, words):
        *init, district = words
        sub = City.parse(init)
        return dict(sub, district=district)


class MicroDistrict(GeoItem):
    order = 50

    @classmethod
    def parse(cls, words):
        *init, microdistrict = words
        sub = City.parse(init)
        return dict(sub, microdistrict=microdistrict)


class Street(GeoItem):
    order = 60

    @classmethod
    def parse(cls, words):
        *init, street = words

        if len(init) == 2 or init[1].endswith(RAIONKEY):
            sub = City.parse(init)
        else:
            sub = District.parse(init)

        return dict(sub, street=street)


class Address(GeoItem):
    order = 70

    @classmethod
    def parse(cls, words):
        *init, address = words
        sub = Street.parse(init)
        return dict(sub, address=address)


TYPES = GeoMeta.registry
