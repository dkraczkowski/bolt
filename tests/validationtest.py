import unittest
from tests.fixtures import ExampleValidator
from bolt.validation import *
from datetime import datetime


class ValidatorObjectTest(unittest.TestCase):

    def test_create_validator(self):

        class UserDetailsValidator(Validator):
            username = EmailValidator()
            password = StringValidator(min=5)

        valid_user = UserDetailsValidator({
            'username': 'test@example.com',
            'password': 'secretpwd'
        })
        self.assertTrue(valid_user.is_valid())

        valid_user = UserDetailsValidator({})
        self.assertTrue(valid_user.is_valid())

        invalid_user = UserDetailsValidator({
            'username': 'invalid',
            'password': 'validpwd'
        })
        self.assertFalse(invalid_user.is_valid())


class ValidatorsTest(unittest.TestCase):

    def test_string_validator(self):

        validator = StringValidator()
        self.assertTrue(validator.validate('test')())
        self.assertFalse(validator.validate(1)())
        self.assertTrue(validator.validate(None)())
        self.assertFalse(validator.validate({})())

        validator = StringValidator(required=True)
        self.assertFalse(validator.validate(None)())
        self.assertTrue(validator.validate('test')())

        validator = StringValidator(min=3)
        self.assertTrue(validator.validate('mmm')())
        self.assertFalse(validator.validate('mm')())
        self.assertTrue(validator.validate(None)())

        validator = StringValidator(max=4)
        self.assertTrue(validator.validate('m')())
        self.assertTrue(validator.validate(None)())
        self.assertFalse(validator.validate('mmmmm')())
        self.assertTrue(validator.validate('mm')())

        validator = StringValidator(min=2, max=4)
        self.assertFalse(validator.validate('m')())
        self.assertTrue(validator.validate('m' * 2)())
        self.assertTrue(validator.validate('m' * 3)())
        self.assertTrue(validator.validate('m' * 4)())
        self.assertFalse(validator.validate('m' * 5)())
        self.assertTrue(validator.validate(None)())

        validator = StringValidator(min=2, max=4, required=True)
        self.assertFalse(validator.validate(None))
        self.assertTrue(validator.validate('m' * 3))
        self.assertFalse(validator.validate('m'))
        self.assertFalse(validator.validate('m' * 5))

    def test_number_validator(self):

        validator = NumberValidator()
        self.assertTrue(validator.validate(1))
        self.assertTrue(validator.validate(1.0))
        self.assertTrue(validator.validate(None))

        validator = NumberValidator(min=1)
        self.assertFalse(validator.validate(0.2))
        self.assertFalse(validator.validate(0))
        self.assertFalse(validator.validate(-1))
        self.assertTrue(validator.validate(1))
        self.assertTrue(validator.validate(1.0))

        validator = NumberValidator(max=2)
        self.assertTrue(validator.validate(2))
        self.assertTrue(validator.validate(1.0))
        self.assertFalse(validator.validate(2.1))
        self.assertFalse(validator.validate(3))

        validator = NumberValidator(min=1, max=2)
        self.assertTrue(validator.validate(2))
        self.assertTrue(validator.validate(1.0))
        self.assertFalse(validator.validate(2.1))
        self.assertFalse(validator.validate(3))
        self.assertFalse(validator.validate(0))

        validator = NumberValidator(allow_decimals=False)
        self.assertTrue(validator.validate(2))
        self.assertFalse(validator.validate(1.0))

    def test_email_validator(self):

        valid_emails = [
            'email@example.com',
            'firstname.lastname@example.com',
            'email@subdomain.example.com',
            'firstname+lastname@example.com',
            'email@123.123.123.123',
            'email@[123.123.123.123]',
            '"email"@example.com',
            'em\'ail@example.com',
            '1234567890@example.com',
            'email@example-one.com',
            '_______@example.com',
            'email@example.name',
            'email@example.museum',
            'email@example.co.jp',
            'firstname-lastname@example.com',
        ]

        invalid_emails = [
            'plainaddress',
            '#@%^%#$@#$@#.com',
            '@example.com',
            'Joe Smith <email@example.com>',
            'email.example.com',
            'email@example@example.com',
            '.email@example.com',
            'email.@example.com',
            'email..email@example.com',
            'あいうえお@example.com',
            'email@-example.com',
            'email@example..com',
            'Abc..123@example.com'
        ]

        validator = EmailValidator()

        for email in valid_emails:
            self.assertTrue(validator.validate(email))

        for email in invalid_emails:
            self.assertFalse(validator.validate(email))

        validator = EmailValidator(allowed_domains=['example.com', 'super.gmail.com'])
        self.assertTrue(validator.validate('example@super.gmail.com'))
        self.assertTrue(validator.validate('example@example.com'))
        self.assertFalse(validator.validate('example@example1.com'))
        self.assertFalse(validator.validate('example@a.com'))
        self.assertFalse(validator.validate('example@[123.123.123.123]'))

    def test_date_validator(self):

        date_format = '%Y/%m/%d'
        validator = DateValidator()
        self.assertTrue(validator.validate('2015-02-01'))
        validator = DateValidator(date_format=date_format)
        self.assertTrue(validator.validate('2015/02/01'))
        self.assertFalse(validator.validate('15/02/01'))
        min = datetime.strptime('2015/02/01', date_format)
        max = datetime.strptime('2015/03/01', date_format)
        validator = DateValidator(min=min, max=max)
        self.assertTrue(validator.validate('2015/02/01'))
        self.assertTrue(validator.validate('2015/03/01'))
        self.assertTrue(validator.validate('2015/02/20'))
        self.assertFalse(validator.validate('2015/03/02'))
        self.assertFalse(validator.validate('2015/01/01'))

    def test_url_validator(self):

        validator = UrlValidator()
        self.assertTrue(validator.validate('example.com'))
        self.assertTrue(validator.validate('http://example.com'))
        self.assertTrue(validator.validate('https://example.com'))
        self.assertTrue(validator.validate('example.com?q=532876%^673'))
        self.assertTrue(validator.validate(None))

        validator = UrlValidator(valid_schemes=('http', 'https'))
        self.assertFalse(validator.validate('example.com'))
        self.assertTrue(validator.validate('http://example.com'))
        self.assertTrue(validator.validate('http://example.com?sad=123%%%45652#234'))
        self.assertFalse(validator.validate('chrome://settings.com'))

        validator = UrlValidator(valid_hosts=('example.com', 'test.me'))
        self.assertTrue(validator.validate('example.com'))
        self.assertTrue(validator.validate('example.com/some/url'))
        self.assertTrue(validator.validate('http://test.me/some/url'))
        self.assertFalse(validator.validate('http://goo.gl/some/url'))

    def test_group_validator(self):
        user_details = GroupValidator(
            username=EmailValidator(),
            password=StringValidator(min=3, max=10),
            portfolio=UrlValidator()
        )

        self.assertTrue(user_details.validate({
            'username': "test@example.com",
            'password': "test123",
            'portfolio': "http://portoflio.my/user_id"
        }))

        self.assertTrue(user_details.validate({
            'username': "test@example.com",
            'password': "test123",
            'portfolio': None
        }))

        self.assertTrue(user_details.validate({
            'username': None,
            'password': None,
            'portfolio': None
        }))

        user_details = GroupValidator(
            username=EmailValidator(required=True),
            password=StringValidator(required=True, min=3, max=10),
            portfolio=UrlValidator()
        )

        self.assertFalse(user_details.validate({
            'username': None,
            'password': None,
            'portfolio': None
        }))

        self.assertFalse(user_details.validate({
            'username': 'test',
            'password': 'test123',
            'portfolio': None
        }))

        self.assertTrue(user_details.validate({
            'username': 'test@example.com',
            'password': 'test123',
            'portfolio': None
        }))

        self.assertFalse(user_details.validate({
            'username': 'test@example.com',
            'password': 'test123',
            'portfolio': 'invalid-url'
        }))

        self.assertTrue(user_details.validate({
            'username': 'test@example.com',
            'password': 'test123',
            'portfolio': 'http://valid.com/url'
        }))
