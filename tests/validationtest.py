import unittest
from tests.fixtures import ExampleValidator
from bolt.validation import StringValidator, NumberValidator, EmailValidator


class ValidateTest(unittest.TestCase):

    def test_create_validator(self):
        validator = ExampleValidator({
            'username': 'test@gmail.com',
            'password': 's3cr3t'
        })
        self.assertEqual('test@gmail.com', validator.username)
        self.assertEqual('s3cr3t', validator.password)

    def test_string_validator(self):

        validator = StringValidator()
        self.assertTrue(validator.validate('test'))
        self.assertFalse(validator.validate(1))
        self.assertTrue(validator.validate(None))
        self.assertFalse(validator.validate({}))

        validator = StringValidator(required=True)
        self.assertFalse(validator.validate(None))
        self.assertTrue(validator.validate('test'))

        validator = StringValidator(min=3)
        self.assertTrue(validator.validate('mmm'))
        self.assertFalse(validator.validate('mm'))
        self.assertTrue(validator.validate(None))

        validator = StringValidator(max=4)
        self.assertTrue(validator.validate('m'))
        self.assertTrue(validator.validate(None))
        self.assertFalse(validator.validate('mmmmm'))
        self.assertTrue(validator.validate('mm'))

        validator = StringValidator(min=2, max=4)
        self.assertFalse(validator.validate('m'))
        self.assertTrue(validator.validate('m' * 2))
        self.assertTrue(validator.validate('m' * 3))
        self.assertTrue(validator.validate('m' * 4))
        self.assertFalse(validator.validate('m' * 5))
        self.assertTrue(validator.validate(None))

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