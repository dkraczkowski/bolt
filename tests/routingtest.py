import unittest
from bolt.router import Rule, Route, RouteMap
import inspect


class Test:
    def listener(self):
        pass


class RoutingTest(unittest.TestCase):
    def testSimpleValidRule(self):
        rule = Rule('/')
        result = rule.match('/')
        self.assertNotEqual(None, result)

        result = rule.match('/incorrect')
        self.assertEqual(None, result)

        rule = Rule('/simple/test')
        result = rule.match('/simple/test')
        self.assertNotEqual(None, result)

        rule = Rule('/simple/{test}')
        result = rule.match('/simple/test')
        self.assertNotEqual(None, result)

    def testComplexValidRule(self):
        rule = Rule('/{some}/{example:numeric}[/conditional[/{another}]]')
        result = rule.match('/test/1')
        self.assertNotEqual(None, result)
        self.assertEqual('test', result['some'])
        self.assertEqual('1', result['example'])

        result = rule.match('/test2/2/conditional')
        self.assertNotEqual(None, result)
        self.assertEqual('test2', result['some'])
        self.assertEqual('2', result['example'])

        result = rule.match('/test3/3/conditional/Iwbis___2389')
        self.assertNotEqual(None, result)
        self.assertEqual('test3', result['some'])
        self.assertEqual('3', result['example'])
        self.assertEqual('Iwbis___2389', result['another'])

    def testInvalidRuleMatcher(self):
        rule = Rule('/{some}/{example:unknown}')
        self.assertRaises(ValueError, rule.match, '/test')

    def testInvalidRuleOptionalFragments(self):
        rule = Rule('/{some}[/{example}')
        self.assertRaises(ValueError, rule.match, '/test')

    def testInvalidRuleParameters(self):
        rule = Rule('/{some}/{example')
        self.assertRaises(ValueError, rule.match, '/test')

    def testRoute(self):
        self.count = 0

        def listener():
            pass

        route = Route('/sample/{pattern}', listener)
        route2 = route.clone()

        self.assertEqual(True, route.match('/sample/uri'))
        self.assertEqual(True, route2.match('/sample/uri2'))

        self.assertEqual({'pattern': 'uri'}, route.params)
        self.assertEqual({'pattern': 'uri2'}, route2.params)

        self.assertEqual(False, route.match('/sample1/uri2'))

    def testRouteMap(self):
        map = RouteMap()
        r1 = Route('/some/{route}', Test.listener)
        r2 = Route('/other/route', Test.listener)
        r3 = Route('/{yet}/another', Test.listener)
        r4 = Route('/more[/complex[/{route}]]', Test.listener)
        r5 = Route('/less/{complex:numeric}[/{route:alphanum}]', Test.listener)
        map.add(r1).add(r2).add(r3).add(r4).add(r5)

        f1 = map.find('/some/test')
        self.assertEqual(r1.name, f1.name)
        self.assertEqual(Test.listener, f1.callback)
        f1 = map.find('/some/123')
        self.assertEqual(r1.name, f1.name)
        f1 = map('/some/12-test')
        self.assertEqual(r1.name, f1.name)

        f2 = map.find('/other/route')
        self.assertEqual(r2.name, f2.name)

        f3 = map.find('/other/another')
        self.assertEqual(r3.name, f3.name)
        f3 = map('/another/another')
        self.assertEqual(r3.name, f3.name)

        f4 = map.find('/more/complex/test')
        self.assertEqual(r4.name, f4.name)
        f4 = map.find('/more')
        self.assertEqual(r4.name, f4.name)
        f4 = map('/more/complex')
        self.assertEqual(r4.name, f4.name)

        f5 = map.find('/less/12')
        self.assertEqual(r5.name, f5.name)
        f5 = map.find('/less/12/a')
        self.assertEqual(r5.name, f5.name)
        f5 = map.find('/less/12/1')
        self.assertEqual(r5.name, f5.name)
        f5 = map.find('/less/12/1a')
        self.assertEqual(r5.name, f5.name)
        f5 = map('/less/12/a1')
        self.assertEqual(r5.name, f5.name)

        f0 = map('/12')
        self.assertIsNone(f0)
        f0 = map('/less')
        self.assertIsNone(f0)
        f0 = map('/less/more/complex/route')
        self.assertIsNone(f0)

        grouped_map = RouteMap()
        grouped_map.add(r1, ['GET']).add(r2).add(r3, ['POST']).add(r4, ['GET'])
        fg = grouped_map('/some/123', ['GET'])
        self.assertEqual(r1.name, fg.name)
        fg = grouped_map('/some/123', ['POST'])
        self.assertIsNone(fg)
        fg = grouped_map('/more', ['GET'])
        self.assertEqual(r4.name, fg.name)
        fg = grouped_map('/more', ['*'])
        self.assertEqual(r4.name, fg.name)
        fg = grouped_map('/more', ['GET', 'POST'])
        self.assertEqual(r4.name, fg.name)