from pynamodb import attributes
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

from constants import READ_CAPACITY_UNITS, WRITE_CAPACITY_UNITS


class NameIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = READ_CAPACITY_UNITS
        write_capacity_units = WRITE_CAPACITY_UNITS
        projection = AllProjection()

    name = attributes.UnicodeAttribute(hash_key=True)


class TagsIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = READ_CAPACITY_UNITS
        write_capacity_units = WRITE_CAPACITY_UNITS
        projection = AllProjection()

    tags = attributes.UnicodeSetAttribute(hash_key=True)


class Gif(Model):
    class Meta:
        table_name = "gifs"
        read_capacity_units = READ_CAPACITY_UNITS
        write_capacity_units = WRITE_CAPACITY_UNITS

    key = attributes.UnicodeAttribute(hash_key=True)
    visits = attributes.NumberAttribute(default=0, range_key=True)
    name_index = NameIndex()
    name = attributes.UnicodeAttribute()
    image_url = attributes.UnicodeAttribute()
    tags_index = TagsIndex()
    tags = attributes.UnicodeSetAttribute()
    ready = attributes.BooleanAttribute(default=False)
