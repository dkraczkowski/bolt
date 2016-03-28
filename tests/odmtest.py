from tests.fixtures import UserEntity, TeamEntity, GroupEntity, EntityA, EntityB, EntityC
from bolt.odm import Entity, Field, Mapper
import unittest


class MapperTest(unittest.TestCase):

    users = [
        {
            'name': 'Bob',
            'number': 17,
            'height': 1.92
        },
        {
            'name': 'Dylan',
            'number': 11,
            'height': 2.02
        },
        {
            'name': 'Kek',
            'height': 1.69
        },
        {
            'name': 'Steve',
            'number': 7
        }
    ]

    teams = [
        {
            'name': 'A Team',
            'stars': 10,
            'creator': users[0],
            'scores': [2.0, 2.2, 3.0, 3.0],
            'members': [users[0]]
        },
        {
            'name': 'B Team',
            'stars': 8,
            'creator': users[1],
            'scores': [1.0, 1.3],
            'members': [users[1], users[2]]
        }
    ]

    groups = [
        {
            'group': {
                'type': 'a',
                'value': 1
            }
        },
        {
            'group': {
                'type': 'b',
                'value': 2
            }
        },
        {
            'group': {
                'type': 'c',
                'value': 3
            }
        }
    ]

    def test_define_entity(self):
        self.assertTrue(issubclass(UserEntity, Entity))

        self.assertTrue(hasattr(UserEntity, '__properties__'))
        self.assertTrue('height' in UserEntity.__properties__)
        self.assertTrue('number' in UserEntity.__properties__)

        self.assertIsInstance(UserEntity.__properties__['name'], Field)
        self.assertIsInstance(UserEntity.__properties__['height'], Field)
        self.assertIsInstance(UserEntity.__properties__['number'], Field)

        self.assertEqual(UserEntity.__properties__['name'].default, None)
        self.assertEqual(UserEntity.__properties__['height'].default, None)
        self.assertEqual(UserEntity.__properties__['number'].default, 0)

    def test_create_entity(self):
        user = UserEntity(name='Bob')

        self.assertTrue(hasattr(user, 'name'))
        self.assertTrue(hasattr(user, 'height'))
        self.assertTrue(hasattr(user, 'number'))

        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.number, 0)
        self.assertEqual(user.height, None)

    def test_hydrate_single(self):
        user_hydrator = Mapper(UserEntity)
        bob = user_hydrator.to_entity(MapperTest.users[0])

        self.assertIsInstance(bob, Entity)
        self.assertIsInstance(bob, UserEntity)

        self.assertTrue(hasattr(bob, 'name'))
        self.assertTrue(hasattr(bob, 'height'))
        self.assertTrue(hasattr(bob, 'number'))

        self.assertEqual(bob.name, 'Bob')
        self.assertEqual(bob.number, 17)
        self.assertEqual(bob.height, 1.92)

    def test_hydrate_multiple(self):
        multiple_user_hydrator = Mapper(UserEntity)
        users = multiple_user_hydrator.to_entity(MapperTest.users)
        self.assertEqual(len(users), 4)

        self.assertEqual(users[0].name, 'Bob')
        self.assertEqual(users[1].name, 'Dylan')
        self.assertEqual(users[2].name, 'Kek')
        self.assertEqual(users[3].name, 'Steve')

    def test_hydrate_nested_entities(self):
        team_hydrator = Mapper(TeamEntity)

        teams = team_hydrator.to_entity(MapperTest.teams)

        self.assertEqual(len(teams), 2)
        self.assertIsInstance(teams[0].creator, UserEntity)
        self.assertIsInstance(teams[1].creator, UserEntity)

    def test_hydrate_map(self):
        map_hydrator = Mapper(GroupEntity)

        groups = map_hydrator.to_entity(MapperTest.groups)

        self.assertEqual(len(groups), 3)
        self.assertIsInstance(groups[0].group, EntityA)
        self.assertIsInstance(groups[1].group, EntityB)
        self.assertIsInstance(groups[2].group, EntityC)

