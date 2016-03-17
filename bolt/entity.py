import copy

class Field:

    @property
    def type(self):
        return self._type

    @property
    def default(self):
        return self._default

    def __init__(self, type, default=None):
        self._type = type
        self._default = default


class EntityMeta(type):
    def __new__(mcs, name, bases, attrs):

        if name == 'Entity':
            klass = type.__new__(mcs, name, bases, attrs)
            return klass

        properties = {}
        for value in bases:
            if issubclass(value, Entity):
                EntityMeta._extract_properties(value.__dict__, properties)

        EntityMeta._extract_properties(attrs, properties)

        attrs['__properties__'] = properties
        klass = type.__new__(mcs, name, bases, attrs)
        return klass

    @staticmethod
    def _extract_properties(attrs, properties):
        for name in attrs:
            value = attrs[name]
            if isinstance(value, Field):
                properties[name] = value


class Entity(metaclass=EntityMeta):
    def __init__(self, **kwargs):
        for name in self.__properties__:
            property = self.__properties__[name]
            if issubclass(Entity, property.type):
                
            else:
                if name in kwargs:
                    setattr(self, name, kwargs[name])
                else:
                    setattr(self, name, copy.deepcopy(property.default))

class Hydrator:

    def __init__(self, entity):
        self._entity = entity
        pass

    def hydrate(self, data):
        if isinstance(data, dict):
            return self._hydrate_one(data)
        elif isinstance(data, list) or isinstance(data, tuple):
            return self._hydrate_many(data)
        else:
            raise TypeError('Cannot hydrate object of type %s' % data.__class__.__name__)

    def _hydrate_one(self, data):
        self._entity['__properties__']

    def _hydrate_many(self, data):
        collection = []
        for index in data:
            collection.append(self._hydrate_one(data[index]))
        return collection


class UserEntity(Entity):
    username = Field(type=str)
    password = Field(type=str, default='No password')


class AggregatingEntity(Entity):
    users = Field(type=UserEntity)
    data = Field(type=list)
    number = Field(type=int)
    long_number = Field(type=float)


user = UserEntity(
    username='test',
    password='sa'
)

another = user