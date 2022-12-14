#
# BeoPlay JSON interface for Bang & Olufsen Speakers, TVs and other NL devices
# Reference: https://documenter.getpostman.com/view/1053298/T1LTe4Lt#intro
# Reference: https://raw.githubusercontent.com/PolyPv/BeoRemote/master/BeoRemote.txt
# Lifted a lot of code from marton borzak's ha-beoplay
#
#
# https://widdowquinn.github.io/coding/update-pypi-package/
#

import requests
import aiohttp
import asyncio
from aiohttp import ClientResponse
import json
import logging
from .const import *


LOG = logging.getLogger(__name__)


class BeoPlay(object):
    def __init__(self, host, session : aiohttp.ClientSession = None):
        self._host = host
        self._host_notifications = BASE_URL.format(self._host, BEOPLAY_URL_NOTIFICATIONS)
        self._connfail = 0
        self._clientsession = session
# device information
        self._name = None
        self._serialNumber = None
        self._typeNumber = None
        self._itemNumber = None
# State and Media information
        self.on = None
        self.min_volume = None
        self.max_volume = None
        self.volume = None
        self.muted = None
        self.state = None
        self.media_url = None
        self.media_track = None
        self.media_artist = None
        self.media_album = None
        self.media_genre = None
        self.media_country = None
        self.media_languages = None
        self.primary_experience = None
# Sources
        self.source = None
        self.sources = []
        self.sourcesID = []
        self.sourcesBorrowed = []
# Stand control
        self.standPosition = None
        self.standPositions = []
        self.standPositionsID = []

    ###############################################################
    # ASYNC BASED INTERACTION
    ###############################################################

    async def async_getReq(self, path):
        try:
            async with self._clientsession.get(BASE_URL.format(self._host, path)) as resp:
                LOG.debug("Request Status: %s",str(resp.status))
                if resp.status != 200:
                    return None
                json = await resp.json()
                LOG.debug("Request Json: %s",json)
                return json
        except requests.exceptions.RequestException as err:
            LOG.debug("Exception: %s", str(err))
            self._connfail = CONNFAILCOUNT
            return False

    async def async_postReq(self, type, path, data):
        try:
            r = None
            if type == "PUT":
                r = self._clientsession.put(BASE_URL.format(self._host, path), data=json.dumps(data), timeout=TIMEOUT)
            if type == "POST":
                if data == '':
                    r = self._clientsession.post(BASE_URL.format(self._host, path), timeout=TIMEOUT)
                else:
                    r = self._clientsession.post(BASE_URL.format(self._host, path), data=json.dumps(data), timeout=TIMEOUT)
            if type == "DELETE":
                r = self._clientsession.delete(BASE_URL.format(self._host, path), timeout=TIMEOUT)
            if r:
                LOG.debug("Response: %s", r.content)
                if r.status_code == 200:
                    return True
            return False
        except requests.exceptions.RequestException as err:
            LOG.debug("Exception: %s", str(err))
            self._connfail = CONNFAILCOUNT
            return False

    async def async_notificationsTask(self, callback = None) -> bool:
        try:
            async with self._clientsession.get(self._host_notifications) as response:
                data = None
                if response.status == 200:
                    while True:
                        data = await response.content.readline()
                        if data and len(data)>0:
                            data = data.decode("utf-8").replace("\r", "").replace("\n", "")
                            if(len(data)>0):
                                LOG.info("Update status: " + self._name + data)
                                data_json = json.loads(data)
                                self._processNotification(data_json)
                                if callback is not None:
                                    callback()
                        else:
                            break
                else:
                    LOG.error(
                        "Error %s on %s.",
                        response.status,
                        self._speaker._host_notifications,
                    )
                    return False

        except (asyncio.TimeoutError, aiohttp.ClientError):
            LOG.info("Client connection error, marking %s as offline", self._name)
            raise

        return True

    async def async_getDeviceInfo(self):
        r = await self.async_getReq("BeoDevice")
        if r:
            self._serialNumber = r["beoDevice"]["productId"]["serialNumber"]
            self._name = r["beoDevice"]["productFriendlyName"]["productFriendlyName"]
            self._typeNumber = r["beoDevice"]["productId"]["typeNumber"]
            self._itemNumber = r["beoDevice"]["productId"]["itemNumber"]

    ###############################################################
    # REQUESTS BASED INTERACTION
    ###############################################################

    def _getReq(self, path):
        try:
            if self._connfail:
                LOG.debug("Connfail: %i", self._connfail)
                self._connfail -= 1
                return False
            r = requests.get(BASE_URL.format(self._host, path), timeout=TIMEOUT)
            if r.status_code != 200:
                return None
            return json.loads(r.text)
        except requests.exceptions.RequestException as err:
            LOG.debug("Exception: %s", str(err))
            self._connfail = CONNFAILCOUNT
            return None

    def _postReq(self, type, path, data):
        try:
            r = None
            if self._connfail:
                LOG.debug("Connfail: %i", self._connfail)
                self._connfail -= 1
                return False
            if type == "PUT":
                r = requests.put(BASE_URL.format(self._host, path), data=json.dumps(data), timeout=TIMEOUT)
            if type == "POST":
                if data == '':
                    r = requests.post(BASE_URL.format(self._host, path), timeout=TIMEOUT)
                else:
                    r = requests.post(BASE_URL.format(self._host, path), data=json.dumps(data), timeout=TIMEOUT)
            if type == "DELETE":
                r = requests.delete(BASE_URL.format(self._host, path), timeout=TIMEOUT)
            if r:
                LOG.debug("Response: %s", r.content)
                if r.status_code == 200:
                    return True
            return False
        except requests.exceptions.RequestException as err:
            LOG.debug("Exception: %s", str(err))
            self._connfail = CONNFAILCOUNT
            return False

    ###############################################################
    # GET ATTRIBUTES FROM THE SPEAKER
    ###############################################################

    def getVolume(self, data):
        if data["notification"]["type"] == "VOLUME" and data["notification"]["data"] is not None:
            self.volume = int(data["notification"]["data"]["speaker"]["level"])/100
            self.min_volume = int(data["notification"]["data"]["speaker"]["range"]["minimum"])/100
            self.max_volume = int(data["notification"]["data"]["speaker"]["range"]["maximum"])/100
            self.muted = data["notification"]["data"]["speaker"]["muted"]

    def getSource(self, data):
        if data["notification"]["type"] == "SOURCE" and data["notification"]["data"] is not None:
            if not data["notification"]["data"]:
                self.source = None
                self.state = None
                self.on = False
            else:
                self.source = data["notification"]["data"]["primaryExperience"]["source"]["friendlyName"]
                self.state = data["notification"]["data"]["primaryExperience"]["state"]
                self.on = True
            self.media_url = None
            self.media_track = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None

    def getPrimaryExperience(self, data):
        if data["notification"]["type"] == "SOURCE":
            self.primary_experience = data["primary"]

    def getState(self, data):
        if data["notification"]["type"] == "PROGRESS_INFORMATION" and data["notification"]["data"]  is not None:
            self.state = data["notification"]["data"]["state"]
            self.on = True

    def getMusicInfo(self, data):
        if data["notification"]["type"] == "NOW_PLAYING_STORED_MUSIC":
            if data["notification"]["data"]["trackImage"]:
                self.media_url = data["notification"]["data"]["trackImage"][0]["url"]
            else:
                self.media_url = None
            self.media_artist = data["notification"]["data"]["artist"]
            self.media_album = data["notification"]["data"]["album"]
            self.media_track = data["notification"]["data"]["name"]
            self.media_genre = None
            self.media_country = None
            self.media_languages = None

        if data["notification"]["type"] == "NOW_PLAYING_NET_RADIO":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            if 'image' in data["notification"]["data"] and data["notification"]["data"]["image"]:
                self.media_url = data["notification"]["data"]["image"][0]["url"]
            if 'name' in data["notification"]["data"]:
                self.media_artist = data["notification"]["data"]["name"]
            if 'liveDescription' in data["notification"]["data"]:
                self.media_track = data["notification"]["data"]["liveDescription"]
            if 'genre' in data["notification"]["data"]:
                self.media_genre = data["notification"]["data"]["genre"]
            if 'country' in data["notification"]["data"]:
                self.media_country = data["notification"]["data"]["country"]
            if 'languages' in data["notification"]["data"]["languages"]:
                self.media_languages = data["notification"]["data"]["languages"]

        if data["notification"]["type"] == "NOW_PLAYING_LEGACY":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            self.media_track = str(data["notification"]["data"]["trackNumber"])
            if data["notification"]["kind"] == "playing":
                self.on = True
            else:
                self.on = False
            self.state = data["notification"]["kind"]

        if data["notification"]["type"] == "NUMBER_AND_NAME":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            self.media_track = str(data["notification"]["data"]["number"]) + ". " + data["notification"]["data"]["name"]

    def _processNotification(self, data):
        ############################################################
        # functions are coming here that update the properties
        ############################################################
        try:
            # get volume
            self.getVolume(data)
            # get source
            self.getSource(data)
            # get state
            self.getState(data)
            # get currently playing music info
            self.getMusicInfo(data)
        except KeyError:
            LOG.debug("Malformed notification: %s", str(data))


    ###############################################################
    # GET ATTRIBUTES FROM THE SPEAKER - BLOCKING CALLS
    ###############################################################

# edited to only include in Use sources
    def getSources(self):
        r = self._getReq('BeoZone/Zone/Sources')
        if r:
            for elements in r:
                i = 0
                while i < len(r[elements]):
                    if r[elements][i][1]["inUse"] == True:
                        self.sourcesBorrowed.append(r[elements][i][1]["borrowed"])
                        self.sources.append(r[elements][i][1]["friendlyName"])
                        self.sourcesID.append(r[elements][i][0])
                    i += 1

    def getStandby(self):
        r = self._getReq('BeoDevice/powerManagement/standby')
        if r:
            if r["standby"]["powerState"] == "on":
                self.on = True
            else:
                self.on = False

    def getStandPosition(self):
        r = self._getReq('BeoZone/Zone/Stand/Active')
        if r:
            if r["active"] is not None:
                self._standPosition = r["active"]

    def getStandPositions(self):
        r = self._getReq('BeoZone/Zone/Stand')
        if r:
            for elements in r:
                i = 0
                while i < len(r[elements]):
                    self.standPositions.append(r[elements][i][1]["friendlyName"])
                    self.standPositionsID.append(r[elements][i][0])
                    i += 1

    def getDeviceInfo(self):
        r = self._getReq("BeoDevice")
        if r:
            self._serialNumber = r["beoDevice"]["productId"]["serialNumber"]
            self._name = r["beoDevice"]["productFriendlyName"]["productFriendlyName"]
            self._typeNumber = r["beoDevice"]["productId"]["typeNumber"]
            self._itemNumber = r["beoDevice"]["productId"]["itemNumber"]

    ###############################################################
    # COMMANDS
    ###############################################################

    def setVolume(self, volume):
        self.volume = volume
        volume = int(volume*100)
        self._postReq('PUT',BEOPLAY_URL_SET_VOLUME, {'level':volume})

    def setMute(self, mute):
        if mute:
            self._postReq('PUT',BEOPLAY_URL_MUTE, {"muted":True})
        else:
            self._postReq('PUT',BEOPLAY_URL_MUTE, {"muted":False})

    def Play(self):
        self._postReq('POST',BEOPLAY_URL_PLAY,'')
        self._postReq('POST',BEOPLAY_URL_PLAY + BEOPLAY_URL_RELEASE,'')

    def Pause(self):
        self._postReq('POST',BEOPLAY_URL_PAUSE,'')
        self._postReq('POST',BEOPLAY_URL_PAUSE+BEOPLAY_URL_RELEASE,'')

    def Stop(self):
        self._postReq('POST',BEOPLAY_URL_STOP,'')
        self._postReq('POST',BEOPLAY_URL_STOP+BEOPLAY_URL_RELEASE,'')

    def Next(self):
        self._postReq('POST',BEOPLAY_URL_FORWARD,'')
        self._postReq('POST',BEOPLAY_URL_FORWARD+BEOPLAY_URL_RELEASE,'')

    def Prev(self):
        self._postReq('POST',BEOPLAY_URL_BACKWARD,'')
        self._postReq('POST',BEOPLAY_URL_BACKWARD+BEOPLAY_URL_RELEASE,'')

    def Standby(self):
        self._postReq('PUT',BEOPLAY_URL_STANDBY, {"standby":{"powerState":"standby"}})
        self.on = False

    def turnOn(self):
        self._postReq('PUT',BEOPLAY_URL_STANDBY, {"standby":{"powerState":"on"}})
        self.on = True

    def setSource(self, source):
        i = 0
        while i < len(self.sources):
            if self.sources[i] == source:
                chosenSource = self.sourcesID[i]
                self._postReq('POST',BEOPLAY_URL_SET_SOURCE, {"primaryExperience":{"source":{"id":chosenSource}}})
            i += 1

    def setStandPosition(self, standPosition):
        i = 0
        while i < len(self.standPositions):
            if self.standPositions[i] == standPosition:
                chosenStandPosition = self.standPositionsID[i]
                self._postReq('PUT',BEOPLAY_URL_SET_STAND, {"active":chosenStandPosition})
            i += 1

    def joinExperience(self):
        self._postReq('POST',BEOPLAY_URL_JOIN_EXPERIENCE,'')

    def leaveExperience(self):
        self._postReq('DELETE',BEOPLAY_URL_LEAVE_EXPERIENCE, '')

    def playQueueItem(self, instantplay: bool, queueItem: dict):
        if instantplay:
            self._postReq('POST',BEOPLAY_URL_PLAYQUEUE + BEOPLAY_URL_PLAYQUEUE_INSTANT,queueItem)
        else:
            self._postReq('POST',BEOPLAY_URL_PLAYQUEUE,queueItem)
