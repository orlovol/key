import re
import typing
import collections

LEVEL_SEP = ", "
NAME_RE = r"[\w-]+(?: +[\w-]+)*?"  # words with hyphens and digits


def cut(string, left="", right=""):
    if string.startswith(left) and string.endswith(right):
        return string[len(left) : -len(right) or None]
    return string


def geoname_re_keys(name):
    return [f"{name}_{key}" for key in "name old type".split()]


def geoname_re(type_, type_name):
    name = fr"(?P<{type_}_name>{NAME_RE})"
    old_name = fr"\(\s*(?P<{type_}_old>{NAME_RE})\s*\)"
    # regex = fr"(?:{name}\s*(?:{old_name}\s*)?(?P<{type_}_type>{type_name})?)?\s*"
    regex = fr"{name}\s*(?:{old_name}\s*)?(?P<{type_}_type>{type_name})?\W*"
    return regex


class Name(typing.NamedTuple):
    name: str
    old_name: str
    type_: str

    def __str__(self):
        return f"{self.name} ({self.old_name})" if self.old_name else self.name

    def __repr__(self):
        return f'"{self}"'

    @property
    def full(self):
        return f"{self} {self.type_}" if self.type_ else self


def make_name(keys, match):
    return Name(*match.group(*keys))


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
            try:
                pattern = parent.regex.pattern
            except AttributeError:
                pattern = ""

            geo._name = name.lower()
            geo._re_keys = geoname_re_keys(geo._name)
            geo.regex = re.compile(pattern + geoname_re(geo._name, geo.type_name))
            geo.registry = {}  # dictionary of created objects

            cls.registry[geo._name] = geo
        return geo


class GeoItem(GeoType, metaclass=GeoMeta):
    _name: str = None  # class lowercase name - csv key
    type_name: str = ""  # geo entity type suffix
    parent: "GeoItem" = None
    children = {}  # FIXME: global for all classes

    def __new__(cls, *args, **kwargs):
        parent = kwargs.pop("parent")
        obj = super().__new__(cls, *args, **kwargs)
        if parent:
            parent.children[obj.name.name] = obj
            cls.parent = parent
        cls.registry[obj.name.name] = obj
        return obj

    @property
    def regname(self):
        return self.name if self.parent is None else f"{self.parent.regname}/{self.name}"


class Region(GeoItem):
    type_name = "область"

    def __new__(cls, geo_id, name, name_uk, parent=None):
        match = cls.regex.fullmatch(name)
        match_uk = cls.regex.fullmatch(name_uk)

        name = make_name(cls._re_keys, match)
        name_uk = make_name(cls._re_keys, match_uk)

        if parent:
            parent_name: Name = make_name(parent._re_keys, match)
            # print(parent_name, parent.registry) #! need grandname
            parent: GeoItem = parent.registry.get(parent_name.name, None)

        return super().__new__(cls, geo_id=geo_id, name=name, name_uk=name_uk, parent=parent)


class Raion(Region):
    type_name = "район"

    def __new__(cls, geo_id, name, name_uk, parent=Region):
        return super().__new__(cls, geo_id, name, name_uk, parent=parent)


class City(Raion):
    def __new__(cls, geo_id, name, name_uk):
        return super().__new__(cls, geo_id, name, name_uk, parent=Raion)


class District(GeoItem):
    pass


class MicroDistrict(GeoItem):
    pass


class Street(GeoItem):
    pass


class Address(GeoItem):
    pass


TYPES = GeoMeta.registry
