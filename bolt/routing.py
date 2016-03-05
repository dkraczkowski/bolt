import re
import copy


class Route:
    def __init__(self, pattern: str, callback):
        """ Provides simplified and more natural way for building regular
        expression which later on can be matched against uri(s).

        Route format must follow the pattern:
            /user/{name}[/{id:numeric}[/nested-route]]
            ^     ^     ^    ^        ^
            |     |     |    |        |
            |     |     |    |        +- Nesting optionals must be enclosed.
            |     |     |    |
            |     |     |    +- Slug will follow the pattern if one is specified after the colon (available patterns:
            |     |     |                                                                           - any
            |     |     |                                                                           - numeric
            |     |     |                                                                           - alpha
            |     |     |                                                                           - alphanum).
            |     |     |
            |     |     +- Optional parts can be specified by using square bracket.
            |     |
            |     +- Slug must start and end with the curly bracket.
            |
            +- Route must start with the trailing slash.

        :param pattern: route pattern
        :param callback: resource to which route is pointing
        """
        self.name = pattern
        self.callback = callback
        self.params = {}
        self._rule = Rule(pattern)

    def match(self, uri: str):
        """ Tests whether uri matches against the rule.
        Returns False if uri is not matching patter otherwise True.
        Valid uri must start with a slash and contain no ending slash

        Example:

            route = Route('/rule/{slug}', listener)
            route.match('/matching/rule')
            route.params.slug <- will contain string 'rule'

        :param uri: valid uri string
        :return: bool
        """
        self.params = self._rule.match(uri)

        if self.params is None:
            return False

        return True

    def clone(self):
        cloned = Route(self.name, self.callback)
        cloned._rule = self._rule
        cloned.params = copy.copy(self.params)
        return cloned


class RouteMap:
    def __init__(self):
        self._routes = {'*': []}

    def __call__(self, uri: str, groups: list=['*']):
        return self.find(uri, groups)

    def add(self, route: Route, groups: list=['*']):
        for group in groups:
            if group not in self._routes:
                self._routes[group] = []

            if route not in self._routes[group]:
                self._routes[group].append(route)

        return self

    def remove(self, route: Route, groups: list=['*']):
        for group in groups:
            if group == '*':
                for group in self._routes:
                    self._routes[group].remove(route)

                return self

            self._routes[group].remove(route)

        return self

    def find(self, uri: str, groups: list=['*']):
        for group in groups:
            if group == '*':
                for group, routes in self._routes.items():
                    for route in routes:
                        if route.match(uri):
                            return route.clone()
                break

            if group not in self._routes:
                return None

            for route in self._routes[group]:
                if route.match(uri):
                    return route.clone()

        return None


class Rule:
    """
    Private package class
    """
    def __init__(self, route: str):
        self._parsed_rule = ParsedRule(route)
        self._params = {}

    def match(self, uri: str):
        if not uri.startswith('/'):
            raise ValueError('Uri must start with /')
        if uri.endswith('/') and len(uri) != 1:
            raise ValueError('Uri cannot end with /')

        results = self._parsed_rule.match(uri)

        if results is None:
            return None

        return self._fetch_params(results)

    def _fetch_params(self, results):
        params = {}
        for property in self._parsed_rule._properties:
            params[property.name] = results.group(property.name)

        return params


class ParsedRule:

    PATTERN_PARSER = '\[?(\/\{(?P<name>[a-z][a-z0-9_]{0,})(?P<pattern>\:\w+)?\})'

    MATCH_RULES = {
        ':any':         '[^\/]+',
        ':numeric':     '[0-9]+',
        ':alpha':       '[a-z]+',
        ':alphanum':    '[a-z0-9]+'
    }

    def __init__(self, rule: str):
        self.raw_rule = rule
        self._properties = []
        self._pattern = None

    def match(self, uri: str):
        if self._pattern is None:
            self._parse()

        return re.match(self._pattern, uri, re.I)

    def _parse(self):
        without_optionals = self.raw_rule.rstrip(']')
        closing_optionals = len(self.raw_rule) - len(without_optionals)
        opening_optionals = without_optionals.count('[')

        if closing_optionals != opening_optionals:
            raise ValueError('Opening and closing optionals are not matching, check your rule %s' % self.raw_rule)

        if self.raw_rule.count('{') != self.raw_rule.count('}'):
            raise ValueError('Slugs are not properly defined, check your rule %s' % self.raw_rule)

        slugs = re.finditer(self.PATTERN_PARSER, without_optionals, flags=re.I)

        for slug in slugs:
            name = slug.group('name')
            pattern = slug.group('pattern') if slug.group('pattern') else ':any'
            if pattern not in self.MATCH_RULES:
                raise ValueError('Rule uses unknown pattern %s, expected one of: %s' % (pattern,
                                 ', '.join(list(self.MATCH_RULES.keys()))))

            self._properties.append(self.RuleProperty(name, self.MATCH_RULES[pattern], slug.group(1)))

        self._pattern = self._build_pattern()

    def _build_pattern(self):
        pattern = self.raw_rule.\
            replace('/', '/').\
            replace('[', '(?:').\
            replace(']', ')?')
        pattern = re.sub(r'/([^{])', r'\/\1', pattern)

        for property in self._properties:
            pattern = pattern.replace(property.raw, '\/(?P<' + property.name + '>' + property.regex + ')')

        return pattern

    class RuleProperty:

        @property
        def regex(self):

            return self._regex

        def __init__(self, name: str, regex: str, raw: str):
            self.name = name
            self.raw = raw
            self._regex = regex
