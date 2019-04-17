import typing


class GeoItem(typing.NamedTuple):
    geo_id: int
    name: str
    name_uk: str


class Region(GeoItem):
    pass


class Raion(GeoItem):
    pass


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
