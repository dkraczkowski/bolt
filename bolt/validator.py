import re
from datetime import datetime, date
from dateutil import parser as date_parser
from bolt.http import Request, Response, HttpException
from bolt.router import Route


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
        self._errors = []
        for prop in properties:
            if prop in data:
                setattr(self, prop, data[prop])
            else:
                setattr(self, prop, None)

    def is_valid(self):
        validators = self.__class__.__dict__['_validators']
        for key in validators:
            validator = validators[key]
            is_valid = validator.validate(getattr(self, key))
            if not is_valid():
                self._errors += is_valid.get_errors()
                return False
        return True

    def get_errors(self):
        return self._errors



class ValidationResult:

    def __init__(self):
        self.valid = None
        self._errors = []

    def __call__(self, valid=None):
        if valid is None:
            return self.valid
        self.valid = valid
        return self

    def is_valid(self):
        return self.valid

    def add_error(self, msg):
        self._errors.append(msg)

    def get_errors(self):
        return self._errors


class ValidationRule:
    def __init__(self, required=False):
        self._required = required
        self._errors = []

    def validate(self, value=None):
        raise RuntimeError(self.__class__.__name__ + '.validate is not defined')

    def required(self, is_required=True):
        self._required = is_required

    def _validate_required(self, value, result:ValidationResult):
        if value is None:
            if self._required:
                result.add_error('%s is required')
                return False
            return True


class RangeAwareValidator:

    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def _validate_range(self, value):
        if self._min is not None and value < self._min:
            return -1

        if self._max is not None and value > self._max:
            return 1

        return 0


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
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if not isinstance(value, str):
            return result(False)

        valid_range = self._validate_range(len(value))
        if valid_range is not 0:
            if valid_range == -1:
                result.add_error('%s is too short')
            else:
                result.add_error('%s is too long')
            return result(False)

        return result(True)


class NumberValidator(ValidationRule, RangeAwareValidator):

    def __init__(self, required=False, min=None, max=None, allow_decimals=True):
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)
        self._allow_decimals = allow_decimals

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if not isinstance(value, int) and not isinstance(value, float):
            result.add_error('%s is not a valid number')
            return result(False)

        if isinstance(value, float) and self._allow_decimals is False:
            result.add_error('%s is a decimal number, integer number expected')
            return result(False)

        valid_range = self._validate_range(value)
        if valid_range is not 0:
            if valid_range is -1:
                result.add_error('%s is too low')
            else:
                result.add_error('%s is too high')
            return result(False)

        return result(True)


class EmailValidator(ValidationRule):

    # RFC-5321 compliant regex
    EMAIL_REGEX = r"^([!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?(\.[0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?)*|\[((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|IPv6:((((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){6}|::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){5}|[0-9A-Fa-f]{0,4}::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){4}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):)?(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){3}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,2}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){2}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,3}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,4}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,5}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,6}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)|(?!IPv6:)[0-9A-Za-z-]*[0-9A-Za-z]:[!-Z^-~]+)])$"

    def __init__(self, required=False, allowed_domains=None):
        ValidationRule.__init__(self, required)
        self._allowed_domains = allowed_domains

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        matches = re.match(EmailValidator.EMAIL_REGEX, value)
        if matches is None:
            result.add_error('%s is not valid email address')
            return result(False)

        domain = matches.group(5)
        if self._allowed_domains is not None and domain not in self._allowed_domains:
            result.add_error('%s is not within accepted domain')
            return result(False)

        return result(True)


class DateValidator(ValidationRule, RangeAwareValidator):

    def __init__(self, required=False, date_format=None, min=None, max=None):
        ValidationRule.__init__(self, required)
        RangeAwareValidator.__init__(self, min, max)
        self._format = date_format

        if self._min and not isinstance(self._min, date):
            raise ValueError(self.__class__.__name__ + '(min=) min parameter must be instance of datetime.date')

        if self._max and not isinstance(self._max, date):
            raise ValueError(self.__class__.__name__ + '(max=) max parameter must be instance of datetime.date')

        if self._format is None:
            self._alternative_format = None
            return

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if self._format is None:
            try:
                date = date_parser.parse(value)
            except ValueError:
                result.add_error('%s is not valid date')
                return result(False)
        else:
            try:
                date = datetime.strptime(value, self._format)

            except ValueError:
                result.add_error('%s is not well formatted date')
                return result(False)

        if self._validate_range(date) is not 0:
            result.add_error('%s is not within valid period')
            return result(False)

        return result(True)


class BoolValidator(ValidationRule):

    BOOL_TRUE = (True, 1, 'yes', 'YES', 'Yes' '1')
    BOOL_FALSE = (False, 0, 'no', 'NO', 'No', '0')

    def __init__(self, required=False):
        ValidationRule.__init__(self, required)

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if value not in BoolValidator.BOOL_TRUE and value not in BoolValidator.BOOL_FALSE:
            result.add_error('%s is not valid boolean expression')
            return result(False)

        return result(True)


class TrueValidator(BoolValidator):

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if value not in BoolValidator.BOOL_TRUE:
            result.add_error('%s is not truthy')
            return result(False)

        return result(True)


class FalseValidator(BoolValidator):

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        if value not in BoolValidator.BOOL_FALSE:
            result.add_error('%s is not falsy')
            return result(False)

        return result(True)


class UrlValidator(ValidationRule):

    URL_REGEX = r"((\w+?)?\:\/\/)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b)([-a-zA-Z0-9@:%_\+.~#?&//=]*)"

    def __init__(self, required=False, valid_schemes=None, valid_hosts=None):
        ValidationRule.__init__(self, required)
        self._valid_schemes = valid_schemes
        self._valid_hosts = valid_hosts

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        matches = re.match(UrlValidator.URL_REGEX, value)
        if matches is None:
            result.add_error('%s is not valid URL')
            return result(False)

        scheme = matches.group(2)
        host = matches.group(3)

        if self._valid_schemes is not None and scheme not in self._valid_schemes:
            result.add_error('%s has invalid scheme')
            return result(False)

        if self._valid_hosts is not None and host not in self._valid_hosts:
            result.add_error('%s contains invalid host')
            return result(False)

        return result(True)


class RegexValidator(ValidationRule):

    def __init__(self, regex, required=False):
        ValidationRule.__init__(self, required)
        self._regex = regex

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        matches = re.match(self._regex, value)
        if matches is None:
            result.add_error('%s does not conform required value')
            return result(False)

        return result(True)


class GroupValidator(ValidationRule):

    def __init__(self, **kwargs):
        self._rules = kwargs

    def validate(self, value=None):
        result = ValidationResult()
        is_valid = self._validate_required(value, result)
        if is_valid is not None:
            return result(is_valid)

        for field in self._rules:
            validator = self._rules[field]
            if field not in value:
                is_valid = validator.validate(None)()
            else:
                is_valid = validator.validate(value[field])()

            if not is_valid:
                result.add_error('%s is not valid')
                return result(False)

        return result(True)


class ValidationService:

    VALIDATOR = 'validator'

    def __call__(self, app):

        @app.before()
        def validate_request(service_locator):
            route = service_locator.get(Route)
            request = service_locator.get(Request)
            validator = route.get(ValidationService.VALIDATOR)
            if validator is None:
                return True

            data = request.body.from_json()
            validator = validator(data)

            if not validator.is_valid():
                raise HttpException('Could not validate request', Response.HTTP_UNPROCESSABLE_ENTITY)
