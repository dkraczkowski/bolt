import re
from datetime import datetime, date
from dateutil import parser as date_parser


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
        self._errors = []

    def validate(self, value=None):
        raise RuntimeError(self.__class__.__name__ + '.validate is not defined')

    def _log_error(self, error: str):
        self._errors.append(error)


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

        if value is None:
            if self._required:
                self._log_error('%s is required')
                return False
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

        if value is None:
            if self._required:
                return False
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
        if value is None:
            if self._required:
                return False
            return True

        matches = re.match(EmailValidator.EMAIL_REGEX, value)
        if matches is None:
            return False

        domain = matches.group(5)
        if self._allowed_domains is not None and domain not in self._allowed_domains:
            return False

        return True


class DateValidator(ValidationRule, RangeAwareValidator):

    def __init__(self, required=False, date_format=None, min=None, max=None):
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)
        self._format = date_format

        if self._min and not isinstance(self._min, date):
            raise ValueError(self.__class__ + '(min=) min parameter must be instance of datetime.date')

        if self._max and not isinstance(self._max, date):
            raise ValueError(self.__class__ + '(max=) max parameter must be instance of datetime.date')

        if self._format is None:
            self._alternative_format = None
            return

    def validate(self, value=None):
        if value is None:
            if self._required:
                return False
            return True

        if self._format is None:
            try:
                date = date_parser.parse(value)

            except ValueError:
                return False
        else:
            try:
                date = datetime.strptime(value, self._format)

            except ValueError:
                return False

        if not self._validate_range(date):
            return False

        return True


class BoolValidator(ValidationRule):

    BOOL_TRUE = (True, 1, 'yes', 'YES', 'Yes' '1')
    BOOL_FALSE = (False, 0, 'no', 'NO', 'No', '0')

    def __init__(self, required=False):
        ValidationRule.__init__(self, required)

    def validate(self, value=None):
        if value is None:
            if self._required:
                return False
            return True

        if value not in BoolValidator.BOOL_TRUE and value not in BoolValidator.BOOL_FALSE:
            return False

        return True


class TrueValidator(BoolValidator):

    def validate(self, value=None):
        if value is None:
            if self._required:
                return False
            return True

        if value not in BoolValidator.BOOL_TRUE:
            return False

        return True


class FalseValidator(BoolValidator):

    def validate(self, value=None):
        if value is None:
            if self._required:
                return False
            return True

        if value not in BoolValidator.BOOL_FALSE:
            return False

        return True


class UrlValidator(ValidationRule):

    URL_REGEX = r"((\w+?)?\:\/\/)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b)([-a-zA-Z0-9@:%_\+.~#?&//=]*)"

    def __init__(self, required=False, valid_schemes=None, valid_hosts=None):
        ValidationRule.__init__(self, required)
        self._valid_schemes = valid_schemes
        self._valid_hosts = valid_hosts

    def validate(self, value=None):
        if value is None:
            if self._required:
                return False
            return True

        matches = re.match(UrlValidator.URL_REGEX, value)
        if matches is None:
            return False

        scheme = matches.group(2)
        host = matches.group(3)

        if self._valid_schemes is not None and scheme not in self._valid_schemes:
            return False

        if self._valid_hosts is not None and host not in self._valid_hosts:
            return False

        return True


class RegexValidator(ValidationRule):

    def __init__(self, regex, required=False):
        ValidationRule.__init__(self, required)
        self._regex = regex

    def validate(self, value=None):
        if not self._required and value is None:
            return True

        matches = re.match(self._regex, value)
        if matches is None:
            return False

        return True


class GroupValidator(ValidationRule):

    def __init__(self, **kwargs):
        self._group = kwargs

    def validate(self, value=None):

        for field in self._group:
            validator = self._group[field]
            if field not in value:
                is_valid = validator.validate(None)
            else:
                is_valid = validator.validate(value[field])

            if not is_valid:
                return False

        return True
