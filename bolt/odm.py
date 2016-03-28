import copy
import pymongo
from datetime import datetime
from dateutil import parser as date_parser
from bson import ObjectId


class Field:
    ALLOWED_TYPES = [int, float, dict, list, tuple, datetime, str, ObjectId]

    @property
    def default(self):
        return self._default

    @property
    def array_strategy(self):
        return self._array

    def get_type(self, discriminator=None):
        return self._type

    def __init__(self, type, default=None, array=None):
        self._type = type
        self._default = default
        self._array = array

    def value(self, value):

        # Check if value has the primitive type defined in entity
        if not isinstance(value, self.get_type()):
            # Cast to desired type
            # Date time can be stored as a string so lets parse it
            if self.get_type() is datetime:
                return date_parser.parse(value)
            else:
                return self.get_type()(value)

        return value


class Id(Field):
    def __init__(self):
        Field.__init__(self, ObjectId)


class Map(Field):

    @property
    def discriminator(self):
        return self._discriminator

    def __init__(self, map=None, discriminator=None, array=True):
        Field.__init__(self, Map, array=array)
        if (map is not None and discriminator is None) or \
           (discriminator is not None and map is None):
            raise AttributeError('Arguments: `map` and `discriminator` cannot be specified separately')
        self._map = map
        self._discriminator = discriminator

    def get_type(self, discriminator=None):
        if discriminator in self._map:
            return self._map[discriminator]
        else:
            return dict


class EntityMeta(type):
    def __new__(mcs, name, bases, attrs):

        if name == 'Entity':
            klass = type.__new__(mcs, name, bases, attrs)
            return klass

        inherited_properties = {}
        properties = {}
        for value in bases:
            if issubclass(value, Entity) and value is not Entity:
                inherited_properties.update(value.__properties__)

        EntityMeta._extract_properties(attrs, properties)

        # Delete definitions from entity
        for name in properties:
            del attrs[name]

        # Find Id
        id = None
        for name in properties:
            property = properties[name]
            if isinstance(property, Id):
                attrs['__id__'] = property

        attrs['__properties__'] = dict(list(inherited_properties.items()) + list(properties.items()))
        klass = type.__new__(mcs, name, bases, attrs)
        return klass

    @staticmethod
    def _extract_properties(attrs, properties):
        for name in attrs:
            value = attrs[name]
            if isinstance(value, Field):
                value.name = name
                properties[name] = value


class Entity(metaclass=EntityMeta):
    def __init__(self, **kwargs):
        self.__persisted__ = False
        for name in self.__properties__:
            prop = self.__properties__[name]
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, copy.deepcopy(prop.default))

    def get_id(self):
        if not hasattr(self, '__id__'):
            return None
        return getattr(self, self.__id__.name)


class Serializable:
    def serialize(self):
        return {}


class Mapper:

    def __init__(self, entity):
        self._entity = entity
        self._properties = self._entity.__properties__
        pass

    def to_entity(self, data):
        if isinstance(data, dict):
            return self._map_one(data)
        elif isinstance(data, list) or isinstance(data, tuple):
            return self._map_many(data)
        else:
            raise TypeError('Cannot hydrate object of type %s' % data.__class__.__name__)

    def from_entity(self, entity):
        if not isinstance(entity, self._entity):
            raise ValueError('Passed argument must be instance of ' + self._entity.__name__)

        result = {}
        for key in self._properties:
            prop = self._properties[key]
            if not hasattr(entity, key):
                result[key] = prop.default
                continue
            value = getattr(entity, key)
            if issubclass(prop.type, Entity):
                if isinstance(value, (list, tuple)):
                    collection = []
                    for item in value:
                        collection.append(Mapper(prop.type).serialize(item))
                    result[key] = collection
                else:
                    result[key] = Mapper(prop.type).serialize(value)
            else:
                result[key] = value

        return result

    def _map_one(self, data):

        hydrated = self._entity()
        for key in self._properties:
            prop = self._properties[key]
            if key not in data:
                setattr(hydrated, key, prop.default)
                continue

            # Mapping sub-document using discriminator
            if isinstance(prop, Map):
                if prop.discriminator in data[key]:
                    prop_type = prop.get_type(data[key][prop.discriminator])
                    if prop_type is not None:
                        setattr(hydrated, key, Mapper(prop_type).to_entity(data[key]))

                continue

            if issubclass(prop.get_type(), Entity):
                if prop.array_strategy is None or \
                   prop.array_strategy is False and isinstance(data[key], dict) or \
                   prop.array_strategy is True and isinstance(data[key], list):
                    setattr(hydrated, key, Mapper(prop.get_type()).to_entity(data[key]))
                else:
                    raise ValueError()

            else:
                setattr(hydrated, key, prop.value(data[key]))

        return hydrated

    def _map_many(self, data):
        collection = []
        for entity in data:
            collection.append(self._map_one(entity))
        return collection


class Cursor(pymongo.cursor.Cursor):
    def __init__(self, *args, **kwargs):
        pymongo.cursor.Cursor.__init__(self, *args, **kwargs)

    def __getitem__(self, index):
        return self._map_to_entity(pymongo.cursor.Cursor.__getitem__(self, index))

    def __iter__(self):
        return self

    def __next__(self):
        return self._map_to_entity(self.next())

    def _map_to_entity(self, data):
        if self.__collection.name in ODM.__using__:
            cls = ODM.__using__[self.__collection.name]
            map = Mapper(cls)
            entity = map.to_entity(data)
            entity.__persisted__ = True
            if hasattr(entity, '__id__'):
                setattr(entity, entity.__id__.name, data['_id'])
            return entity

        return data


class Query(pymongo.collection.Collection):
    def __init__(self, *args, **kwargs):
        pymongo.collection.Collection.__init__(self, *args, **kwargs)

    def find(self, *args, **kwargs):
        return Cursor(self, *args, **kwargs)

    def persist(self, entity: Entity):
        if not isinstance(entity, Entity):
            raise ValueError('Can persist only entities')
        if not hasattr(entity, '__collection__'):
            raise ValueError('Entity is not assigned to any collection, please refer ODM.use() for further information')
        if entity.__collection__ != self.name:
            raise ValueError('Passed entity have to be persisted in %s collection' % entity.__collection__)

        cls = ODM.__using__[self.name]
        data = Mapper(cls).from_entity(entity)
        if entity.__persisted__ is False:
            self.insert_one(data)
        else:
            self.replace_one({'_id': entity.get_id()}, data)


class ODM:
    __using__ = {}
    _connections = {}
    _default_connection_name = 'default'

    @staticmethod
    def set_default_connection(name):
        ODM._default_connection_name = name

    @staticmethod
    def add_connection(connection: pymongo.MongoClient, name='default'):
        ODM._connections[name] = connection

    @staticmethod
    def get_connection(name=None):
        name = name or ODM._default_connection_name
        return ODM._connections[name]

    @staticmethod
    def remove_connection(name='default'):
        del ODM._connections[name]

    @staticmethod
    def has_connections():
        return len(list(ODM._connections.keys())) > 0

    @staticmethod
    def use(collection):
        def decorator(cls):
            cls.__collection__ = collection
            ODM.__using__[collection] = cls
            return cls
        return decorator


class QueryCommand:

    def __init__(self):
        self._connection = ODM.get_connection()

    def __call__(self, *args, **kwargs):
        pass

    def __getitem__(self, name):
        database = self._connection.get_default_database()
        return Query(database, name)
