from tests.fixtures import SimpleTestObject
from bolt import utils
import unittest
import inspect


class UtilTest(unittest.TestCase):
    def test_call_object_method_args(self):
        test = SimpleTestObject()
        utils.call_object_method(test, 'test_method', 2, 3, 4)
        self.assertEqual(2, test.a)
        self.assertEqual(3, test.b)
        self.assertEqual(4, test.c)

    def test_call_object_method_kwargs(self):
        test = SimpleTestObject()
        utils.call_object_method(test, 'test_method', a=2, b=3, c=4)
        self.assertEqual(2, test.a)
        self.assertEqual(3, test.b)
        self.assertEqual(4, test.c)

    def test_get_fqn(self):
        fqn = utils.get_fqn(SimpleTestObject)
        self.assertEqual('tests.fixtures.SimpleTestObject', fqn)

        fqn = utils.get_fqn(UtilTest)
        self.assertEqual('utilstest.UtilTest', fqn)

    def test_get_method_class(self):
        clsname = utils.find_class(UtilTest.test_get_method_class)
        self.assertEqual(UtilTest, clsname)

        clsname = utils.find_class(self.test_get_fqn)
        self.assertEqual(UtilTest, clsname)

    def test_find_class_name(self):

        classname = utils.find_clsname(UtilTest.test_get_method_class)
        self.assertEqual('UtilTest', classname)
