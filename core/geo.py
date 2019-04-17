import typing

LEVEL_SEP = ", "


def cut(string, left="", right=""):
    if string.startswith(left) and string.endswith(right):
        return string[len(left) : -len(right) or None]
    return string


class GeoItem(typing.NamedTuple):
    geo_id: int
    name: str
    name_uk: str
    type_name: str = ""
    parent: "GeoItem" = None

    @classmethod
    def rcut(cls, string):
        """Cut string suffix"""
        s = f" {cls.type_name}"
        return cut(string, right=s)

    @property
    def fullname(self):
        return f"{self.name} {self.type_name}"

    @property
    def fullname_uk(self):
        return f"{self.name_uk} {self.type_name}"

    @property
    def regname(self):
        if self.parent is None:
            return self.name
        return f"{self.parent.regname}/{self.name}"

class Region(GeoItem):
    type_name = "область"
    registry = {}

    def __new__(cls, geo_id, name, name_uk):
        obj = super().__new__(
            cls,
            geo_id=geo_id,
            name=cls.rcut(name),
            name_uk=cls.rcut(name_uk),
            type_name=cls.type_name,
        )
        cls.registry[obj.regname] = obj
        return obj

    @classmethod
    def from_name(cls, name):
        return cls.registry.get(cls.rcut(name), name)


class Raion(GeoItem):
    type_name = "район"
    registry = {}

    def __new__(cls, geo_id, name, name_uk):
        # print(geo_id, name, name_uk, Region.registry[name])
        parent, _, name = name.partition(LEVEL_SEP)
        *_, name_uk = name_uk.partition(LEVEL_SEP)

        parent = Region.from_name(parent)
        name = cls.rcut(name)
        name_uk = cls.rcut(name_uk)

        obj = super().__new__(
            cls, geo_id=geo_id, name=name, name_uk=name_uk, type_name=cls.type_name, parent=parent
        )

        cls.registry[obj.regname] = obj
        return obj


class City(GeoItem):
    pass


class District(GeoItem):
    pass


class MicroDistrict(GeoItem):
    pass


class Street(GeoItem):
    pass


class Address(GeoItem):
    pass


TYPES = {c.__name__.lower(): c for c in GeoItem.__subclasses__()}
