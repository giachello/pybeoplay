"""Offline regression tests for speaker groups and multiroom expansion."""
import unittest
from unittest.mock import AsyncMock, Mock

from pybeoplay import BeoPlay

GROUP_URL = 'BeoZone/Zone/Sound/SpeakerGroup'
EXPAND_URL = 'BeoZone/Zone/ActiveSources/primaryExperience'
GROUPS = {'speakerGroup': {'active': 0, 'list': [
    {'id': 0, 'friendlyName': 'Start-up'},
    {'id': 1, 'friendlyName': 'Cinema'},
]}}


class SpeakerGroupsTest(unittest.TestCase):
    def setUp(self):
        self.device = BeoPlay('localhost')
        self.device._getReq = Mock(return_value=GROUPS)
        self.device._postReq = Mock(return_value=True)

    def test_get_and_select(self):
        self.assertTrue(self.device.setSpeakerGroup('Start-up'))
        self.device._getReq.assert_called_once_with(GROUP_URL)
        self.device._postReq.assert_called_once_with(
            'PUT', GROUP_URL + '/Active', {'active': 0})
        self.assertEqual(self.device.speakerGroup, 'Start-up')
        self.assertEqual(self.device.speakerGroups, {'Start-up': 0, 'Cinema': 1})
        self.assertEqual(self.device.getSpeakerGroup(), 'Start-up')

    def test_refresh_and_unavailable(self):
        self.device.getSpeakerGroups()
        self.device._getReq.return_value = {'speakerGroup': {'list': [], 'active': None}}
        self.assertEqual(self.device.getSpeakerGroups(), {})
        self.assertIsNone(self.device.speakerGroup)
        with self.assertRaises(ValueError):
            self.device.setSpeakerGroup('Cinema')
        self.device._postReq.assert_not_called()
        for response in (None, {}, {'speakerGroup': None}):
            self.device._getReq.return_value = response
            self.assertIsNone(self.device.getSpeakerGroups())

    def test_expand(self):
        self.assertTrue(self.device.expand('device@example.com'))
        self.device._postReq.assert_called_once_with(
            'POST', EXPAND_URL, {'listener': {'jid': 'device@example.com'}})
        self.device._postReq.return_value = False
        self.assertFalse(self.device.expand('device@example.com'))


class AsyncSpeakerGroupsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.device = BeoPlay('localhost')
        self.device.async_getReq = AsyncMock(return_value=GROUPS)
        self.device.async_postReq = AsyncMock(return_value=True)

    async def test_get_and_select(self):
        self.assertTrue(await self.device.async_set_speaker_group('Start-up'))
        self.device.async_getReq.assert_awaited_once_with(GROUP_URL)
        self.device.async_postReq.assert_awaited_once_with(
            'PUT', GROUP_URL + '/Active', {'active': 0})
        self.assertEqual(await self.device.async_get_speaker_group(), 'Start-up')
        self.assertEqual(self.device.speakerGroups, {'Start-up': 0, 'Cinema': 1})

    async def test_refresh_and_unavailable(self):
        await self.device.async_get_speaker_groups()
        self.device.async_getReq.return_value = {'speakerGroup': {'list': []}}
        self.assertEqual(await self.device.async_get_speaker_groups(), {})
        self.assertIsNone(self.device.speakerGroup)
        with self.assertRaises(ValueError):
            await self.device.async_set_speaker_group('Cinema')
        self.device.async_postReq.assert_not_awaited()
        self.device.async_getReq.return_value = None
        self.assertIsNone(await self.device.async_get_speaker_groups())

    async def test_expand(self):
        self.assertTrue(await self.device.async_expand('device@example.com'))
        self.device.async_postReq.assert_awaited_once_with(
            'POST', EXPAND_URL, {'listener': {'jid': 'device@example.com'}})
        self.device.async_postReq.return_value = False
        self.assertFalse(await self.device.async_expand('device@example.com'))
