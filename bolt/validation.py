import re
from datetime import datetime

class ValidatorMeta(type):

    def __new__(mcs, name, bases, attrs):

        if name == 'Validator':
            klass = type.__new__(mcs, name, bases, attrs)
            return klass

        validators = {}
        for value in bases:
            if issubclass(value, Validator):
                ValidatorMeta._get_validators(value.__dict__, validators)

        ValidatorMeta._get_validators(attrs, validators)

        properties = list(validators.keys())
        properties.sort()

        attrs['_validators'] = validators
        attrs['_properties'] = properties

        klass = type.__new__(mcs, name, bases, attrs)

        return klass

    @staticmethod
    def _get_validators(attrs, validators):
        for name in attrs:
            value = attrs[name]
            if isinstance(value, ValidationRule):
                validators[name] = value


class Property:

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance[self.name]


class Validator(metaclass=ValidatorMeta):

    def __init__(self, data):
        properties = self.__class__.__dict__['_properties']
        for prop in properties:
            if prop in data:
                setattr(self, prop, data[prop])
            else:
                setattr(self, prop, None)

    def is_valid(self):
        validators = self.__class__.__dict__['_validators']


class ValidationRule:
    def __init__(self, required=False):
        self._required = required

    def validate(self, value=None):
        raise RuntimeError(self.__class__.__name__ + '.validate is not defined')


class RangeAwareValidator:

    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def _validate_range(self, value):
        if self._min is not None and value < self._min:
            return False

        if self._max is not None and value > self._max:
            return False

        return True


class StringValidator(ValidationRule, RangeAwareValidator):

    def __init__(self, required=False, min=None, max=None):
        """ Validates string value
        :param required: is required
        :param min: Minimum string length
        :param max: Maximum string length
        :return:
        """
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)

    def validate(self, value=None):

        if not self._required and value is None:
            return True

        if not isinstance(value, str):
            return False

        if not self._validate_range(len(value)):
            return False

        return True


class NumberValidator(ValidationRule, RangeAwareValidator):

    def __init__(self, required=False, min=None, max=None, allow_decimals=True):
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)
        self._allow_decimals = allow_decimals

    def validate(self, value=None):

        if not self._required and value is None:#@todo: fix me
            return True

        if not isinstance(value, int) and not isinstance(value, float):
            return False

        if isinstance(value, float) and self._allow_decimals is False:
            return False

        if not self._validate_range(value):
            return False

        return True


class EmailValidator(ValidationRule):

    # RFC-5321 compliant regex
    EMAIL_REGEX = r"^([!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?(\.[0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?)*|\[((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|IPv6:((((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){6}|::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){5}|[0-9A-Fa-f]{0,4}::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){4}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):)?(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){3}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,2}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){2}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,3}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,4}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,5}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,6}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)|(?!IPv6:)[0-9A-Za-z-]*[0-9A-Za-z]:[!-Z^-~]+)])$"

    def __init__(self, required=False, allowed_domains=None):
        ValidationRule.__init__(self, required)
        self._allowed_domains = allowed_domains

    def validate(self, value=None):
        if not self._required and value is None:
            return True

        matches = re.match(EmailValidator.EMAIL_REGEX, value)
        if matches is None:
            return False

        domain = matches.group(5)
        if self._allowed_domains is not None and domain not in self._allowed_domains:
            return False

        return True


class DateValidator(ValidationRule):

    DATE_FORMAT = {
        'YYYY': '%Y',
        'yyyy': '%Y',
        'YY': '%y',
        'yy': '%y',
        'MM': '%m',
        'mm': '%m',
        'MMM': '',
        'dd': '%d',
        'DD': '%d',
        'ddd': '%s',
        'dddd': '%A',
        'HH': '%H',
        'hh': '%H',
        'H': '%I',
        'h': '%I',
        'SS': '%s',
        'ss': '%s',
        '': '%I',


    }

    def __init__(self, required=False, date_format=None, min=None, max=None):
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)
        self._format = date_format

    def validate(self, value=None):
        pass
