"""

BeoPlay JSON interface for Bang & Olufsen Speakers, TVs and other NL devices
Reference: https://documenter.getpostman.com/view/1053298/T1LTe4Lt#intro
Reference: https://raw.githubusercontent.com/PolyPv/BeoRemote/master/BeoRemote.txt
Lifted a lot of code from marton borzak's ha-beoplay

https://widdowquinn.github.io/coding/update-pypi-package/

"""

import requests
import aiohttp
import asyncio
from aiohttp import ClientResponse
import json
import logging
from typing import Optional
from .const import *


LOG = logging.getLogger(__name__)


class BeoPlay(object):
    def __init__(self, host, session: Optional[aiohttp.ClientSession] = None):
        """Initializes a BeoPlay connection to the speaker / TV
        Host: the IP address of the speaker
        Session (optional): a asyncio client session to be used for async
        communication with the speaker (if not provided, only blocking calls 
        using Requests will work)
        """
        # network information
        self._host = host
        self._host_notifications = BASE_URL.format(
            self._host, BEOPLAY_URL_NOTIFICATIONS
        )
        self._connfail = 0
        self._clientsession = session
        # The following are only going ot be valid after a call to getDeviceInfo
        # device information
        self._name = None
        self._serialNumber = None
        self._typeNumber = None
        self._itemNumber = None
        self._typeName = None
        self._softwareVersion = None
        self._hardwareVersion = None
        # The following are only going ot be valid after a call to getMediaInfo, getStandby
        # Or, they are updated by the Notifications task. The actual field updated by
        # Notifications varies by device. Some devices for example provide notifications when
        # Sound mode changes (e.g., Stage), others (e.g., BeoVision Avant 55) don't.
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
        # The following are only going ot be valid after a call to getSources
        # Sources
        self.source = None
        self.sources = []
        self.sourcesID = []
        self.sourcesBorrowed = []
        self.listeners = []
        # The following are only going ot be valid after a call to getSoundModes
        # Sound modes
        self._soundMode = None
        self._soundModes = {}
        # The following are only going ot be valid after a call to getStandPosition
        # Stand control
        self._standPosition = None
        self._standPositions = {}

    @property
    def host(self):
        """Return the device host."""
        return self._host
    
    @property
    def name(self):
        """Return the device name."""
        return self._name

    @property
    def serialNumber(self):
        """Return the device serial number."""
        return self._serialNumber

    @property
    def itemNumber(self):
        """Return the device serial number."""
        return self._itemNumber

    @property
    def typeNumber(self):
        """Return the device type model number."""
        return self._typeNumber

    @property
    def typeName(self):
        """Return the device type name."""
        return self._typeName

    @property
    def softwareVersion(self):
        """Return the device serial number."""
        return self._softwareVersion

    @property
    def hardwareVersion(self):
        """Return the device serial number."""
        return self._hardwareVersion

    @property
    def remote_commands(self):
        """Get the list of available remote commands"""
        return BEOPLAY_REMOTE_COMMANDS

    @property
    def digits(self):
        """Get the list of available digits"""
        return BEOPLAY_DIGITS
    
    @property
    def soundMode(self):
        """Get the current sound modes"""
        return self._soundMode
    
    @property
    def soundModes(self):
        """Get the list of available sound modes"""
        return list(self._soundModes.keys())
    
    @property
    def soundModesID(self):
        """Get the list of available sound mode IDs"""
        return list(self._soundModes.values())

    @property
    def standPosition(self):
        """Get the current stand position"""
        return self._standPosition
    
    @property
    def standPositions(self):
        """Get the list of available stand positions"""
        return self._standPositions
    
    ###############################################################
    # ASYNC BASED NETWORK CALLS
    ###############################################################

    async def async_getReq(self, path):
        """Non blocking GET call to the speaker, with a given path."""
        if self._clientsession is None:
            LOG.error("Attempt asyncio with no ClientSession")
            return
        try:
            async with self._clientsession.get(
                BASE_URL.format(self._host, path)
            ) as resp:
                LOG.debug("Request Status: %s", str(resp.status))
                if resp.status != 200:
                    return None
                json = await resp.json()
                LOG.debug("Request Json: %s", json)
                return json
        except (asyncio.TimeoutError, aiohttp.ClientError) as _e:
            LOG.info("Client error %s on %s" , str(_e), self._name)
            raise

    async def async_postReq(self, type, path, jsondata: dict = {}):
        """Non blocking POST call to the speaker, with a given path and JSON data.
        type: PUT POST or DELETE
        path: the path of the request
        data: JSON data for the POST, in the form of Python dict/arrays
        """
        if self._clientsession is None:
            LOG.error("Attempt asyncio with no ClientSession")
            return
        try:
            if type == "PUT":
                async with self._clientsession.put(
                    BASE_URL.format(self._host, path), json=jsondata, timeout=aiohttp.ClientTimeout(total=TIMEOUT)
                ) as resp:
                    LOG.debug("Status: %s", resp.status)
                    if resp.status != 200:
                        return False
            elif type == "POST":
                async with self._clientsession.post(
                    BASE_URL.format(self._host, path), json=jsondata, timeout=aiohttp.ClientTimeout(total=TIMEOUT)
                ) as resp:
                    LOG.debug("Status: %s", resp.status)
                    if resp.status != 200:
                        return False
            elif type == "DELETE":
                async with self._clientsession.delete(
                    BASE_URL.format(self._host, path), timeout=aiohttp.ClientTimeout(total=TIMEOUT)
                ) as resp:
                    LOG.debug("Status: %s", resp.status)
                    if resp.status != 200:
                        return False

            else:
                return False
        except (asyncio.TimeoutError, aiohttp.ClientError) as _e:
            LOG.info("Client error %s on %s" , str(_e), self._name)
            raise
        return True

    async def async_notificationsTask(self, callback=None) -> bool:
        """
        Async notifications taks that can be used to keep track of the speaker actions.
        B&O speakers disconnect after 5 minutes of inactivity, so restart the task if this exits.
        This function automatically updates the internal state of the BeoPlay object.

        callback: a function to be called to use the notification (E.g. to update a UI...)
        """
        if self._clientsession is None:
            LOG.error("Attempt asyncio with no ClientSession")
            return False
        try:
            async with self._clientsession.get(self._host_notifications) as response:
                data = None
                if response.status == 200:
                    while True:
                        data = await response.content.readline()
                        if data and len(data) > 0:
                            data = (
                                data.decode("utf-8").replace("\r", "").replace("\n", "")
                            )
                            if len(data) > 0:
                                LOG.info("Update status: %s %s", self._name, data)
                                data_json = json.loads(data)
                                self._processNotification(data_json)
                                if callback is not None:
                                    callback(data_json["notification"])
                        else:
                            break
                else:
                    LOG.error(
                        "Error %s on %s.",
                        response.status,
                        self._host_notifications,
                    )
                    return False

        except (asyncio.TimeoutError, aiohttp.ClientError) as _e:
            LOG.info("Client error %s on %s" , str(_e), self._name)
            raise

        return True

    ###############################################################
    # GET ATTRIBUTES FROM THE SPEAKER - NON-BLOCKING CALLS
    ###############################################################

    async def async_get_source(self):
        """Returns the current source, or None if not retrieved."""
        self.source = None
        r = await self.async_getReq(BEOPLAY_URL_ACTIVE_SOURCES)
        if r:
            self.source = r["primaryExperience"]["source"]["friendlyName"] if "friendlyName" in r["primaryExperience"]["source"] else None
            self.listeners = [listener["jid"] for listener in r["primaryExperience"]["listenerList"]["listener"]] if "listenerList" in r["primaryExperience"] else []
        return self.source

    # edited to only include in Use sources
    async def async_get_sources(self):
        """Returns a list of available sources, or None if not retrieved."""
        r = await self.async_getReq(BEOPLAY_URL_GET_SOURCES)
        if r:
            # clear previously stored sources
            self.sources = []
            self.sourcesID = []
            self.sourcesBorrowed = []
            for elements in r:
                i = 0
                while i < len(r[elements]):
                    if r[elements][i][1]["inUse"] == True:
                        self.sourcesBorrowed.append(r[elements][i][1]["borrowed"])
                        self.sources.append(r[elements][i][1]["friendlyName"])
                        self.sourcesID.append(r[elements][i][0])
                    i += 1
            return self.sources
        return

    async def async_get_standby(self) -> bool:
        """Returns True of the device is on, False if off or unavailable."""
        r = await self.async_getReq(BEOPLAY_URL_STANDBY)
        if r:
            if r["standby"]["powerState"] == "on":
                self.on = True
            else:
                self.on = False
            return self.on
        return False
    
    async def async_get_sound_mode(self):
        """Returns the current sound mode, or None if not retrieved."""
        self._soundMode = None
        await self.async_get_sound_modes()
        return self._soundMode

    async def async_get_sound_modes(self):
        """Returns a dictionary of available sound modes, or None if not retrieved."""
        r = await self.async_getReq(BEOPLAY_URL_GET_SOUND_MODE)
        if r:
            r = r.get("mode", {"list": []})
            l = r.get("list", [])
            a = r.get("active", None)
            for element in l:
                self._soundModes[element["friendlyName"]] = element["id"]
                if a and a == element["id"]:
                    self._soundMode = element["friendlyName"]
            return self._soundModes
        return
    
    async def async_get_stand_position(self):
        """Returns the stand position, or None if not retrieved."""
        self._standPosition = None
        r = await self.async_getReq(BEOPLAY_URL_STAND_ACTIVE)
        if r and "active" in r:
            if r["active"] is not None:
                self._standPosition = r["active"]
            return self._standPosition
        return

    async def async_get_stand_positions(self):
        """Returns a list of available stand positions, or None if not retrieved."""
        # clear previous stand positions
        self._standPositions = {}
        r = await self.async_getReq(BEOPLAY_URL_STAND)
        if r and "stand" in r:
            if r["stand"] is not None:
                for elements in r["stand"]["list"]:
                    self._standPositions[elements["friendlyName"]] = elements["id"]
                return self._standPositions
        return

    async def async_get_device_info(self):
        """Returns a tuple serialNumber, name, typeNumber, itemNumber"""
        r = await self.async_getReq("BeoDevice")
        if r:
            self._serialNumber = r["beoDevice"]["productId"]["serialNumber"]
            self._name = r["beoDevice"]["productFriendlyName"]["productFriendlyName"]
            self._typeNumber = r["beoDevice"]["productId"]["typeNumber"]
            self._itemNumber = r["beoDevice"]["productId"]["itemNumber"]
            self._softwareVersion = r["beoDevice"]["software"]["version"]
            self._hardwareVersion = r["beoDevice"]["hardware"]["version"]
            self._typeName = r["beoDevice"]["productId"]["productType"]
            return self._serialNumber, self._name, self._typeNumber, self._itemNumber
        return

    ###############################################################
    # COMMANDS - Non Blocking
    ###############################################################

    async def async_set_volume(self, volume):
        self.volume = volume
        volume = int(volume * 100)
        await self.async_postReq("PUT", BEOPLAY_URL_SET_VOLUME, {"level": volume})

    async def async_set_mute(self, mute):
        if mute:
            await self.async_postReq("PUT", BEOPLAY_URL_MUTE, {"muted": True})
        else:
            await self.async_postReq("PUT", BEOPLAY_URL_MUTE, {"muted": False})

    async def async_play(self):
        await self.async_postReq("POST", BEOPLAY_URL_PLAY, {})

    async def async_pause(self):
        await self.async_postReq("POST", BEOPLAY_URL_PAUSE, {})

    async def async_stop(self):
        await self.async_postReq("POST", BEOPLAY_URL_STOP, {})

    async def async_stepup(self):
        await self.async_postReq("POST", BEOPLAY_URL_STEPUP, {})

    async def async_stepdown(self):
        await self.async_postReq("POST", BEOPLAY_URL_STEPDOWN, {})

    async def async_forward(self):
        await self.async_postReq("POST", BEOPLAY_URL_FORWARD, {})

    async def async_backward(self):
        await self.async_postReq("POST", BEOPLAY_URL_BACKWARD, {})

    async def async_shuffle(self):
        await self.async_postReq("POST", BEOPLAY_URL_SHUFFLE, {})

    async def async_repeat(self):
        await self.async_postReq("POST", BEOPLAY_URL_REPEAT, {})

    async def async_standby(self):
        await self.async_postReq(
            "PUT", BEOPLAY_URL_STANDBY, {"standby": {"powerState": "standby"}}
        )
        self.on = False

    async def async_turn_on(self):
        """Turn on the device. There is no such thing as an "on" command on B&O 
        equipment, so just select the first source, if it exists."""
        if len(self.sources)>0:
            await self.async_set_source(self.sources[0])
            self.on = True

    async def async_set_source(self, source):
        i = 0
        while i < len(self.sources):
            if self.sources[i] == source:
                chosenSource = self.sourcesID[i]
                await self.async_postReq(
                    "POST",
                    BEOPLAY_URL_ACTIVE_SOURCES,
                    {"primaryExperience": {"source": {"id": chosenSource}}},
                )
            i += 1

    async def async_set_sound_mode(self, soundMode):
        # get sound modes if not already done
        if not self._soundModes:
            await self.async_get_sound_modes()
        
        if soundMode not in self._soundModes:
            raise ValueError("Sound mode not available")
        
        soundModeId = self._soundModes[soundMode]
        
        await self.async_postReq("PUT", BEOPLAY_URL_SET_SOUND_MODE, {"active": soundModeId})
            

    async def async_set_stand_position(self, standPosition):
        if not self._standPositions:
            await self.async_get_stand_positions()
        
        if standPosition not in self._standPositions:
            raise ValueError("Stand position not available")

        standPositionID = self._standPositions.get(standPosition, None)

        await self.async_postReq("PUT", BEOPLAY_URL_STAND_ACTIVE, {"active": standPositionID})

    async def async_join_experience(self):
        await self.async_postReq("POST", BEOPLAY_URL_JOIN_EXPERIENCE)

    async def async_leave_experience(self):
        await self.async_postReq("DELETE", BEOPLAY_URL_LEAVE_EXPERIENCE)

    async def async_play_queue_item(self, instantplay: bool, queueItem: dict):
        """Play a queue item, from Deezer, TuneIn or DLNA.
        TuneIn Dict structure:
            "playQueueItem": {
               "behaviour": "planned",
                "station": {
                    "tuneIn": {
                    "stationId": "s45455"
                    },
                    "image" : []
                }
            }

        Deezer:
            "playQueueItem": {
                "behaviour": "impulsive",
                "track": {
                    "deezer": {
                        "id": 997764
                    },
                    "image" : []
                }
            }

        DLNA:
            "playQueueItem": {
                "behaviour": "impulsive",
                "track": {
                    "dlna": {
                        "url": "http://192.168.100.124:50599/disk/NON-DLNA-OP01-FLAGS01700000/O0$1$8I96439051.m4a"
                    }
                }
            }

        """
        if instantplay:
            await self.async_postReq(
                "POST", BEOPLAY_URL_PLAYQUEUE + BEOPLAY_URL_PLAYQUEUE_INSTANT, queueItem
            )
        else:
            await self.async_postReq("POST", BEOPLAY_URL_PLAYQUEUE, queueItem)

    async def async_remote_command(self, command : str, toBeReleased :bool = False):
        """
        Send a remote command to the device. Command needs to be one of:  

        Cursor/Select, Cursor/Up, Cursor/Down, Cursor/Left, Cursor/Right, Cursor/Exit, Cursor/Back, Cursor/PageUp, Cursor/PageDown, Cursor/Clear, 
        Stream/Play, Stream/Stop, Stream/Pause, Stream/Wind, Stream/Rewind, Stream/Forward, Stream/Backward, 
        List/StepUp, List/StepDown, List/PreviousElement, List/Shuffle, List/Repeat, 
        Menu/Root, Menu/Option, Menu/Setup, Menu/Contents, Menu/Favorites, Menu/ElectronicProgramGuide, Menu/VideoOnDemand, Menu/Text, Menu/HbbTV,Menu/HomeControl, 
        Device/Information, Device/Eject, Device/TogglePower, Device/Languages, Device/Subtitles, Device/OneWayJoin, Device/Mots, 
        Record/Record, 
        Generic/Blue, Generic/Red, Generic/Green, Generic/Yellow.
        
        toBeReleased: true if this is a button press that is held. Needs to be completed by calling async_remote_release.

        """
        if (command not in BEOPLAY_REMOTE_COMMANDS):
            return
        await self.async_postReq("POST", BEOPLAY_REMOTE_PREFIX + command, {"toBeReleased": toBeReleased})

    async def async_remote_release(self, command : str):
        if (command not in BEOPLAY_REMOTE_COMMANDS):
            return
        await self.async_postReq("POST", BEOPLAY_REMOTE_PREFIX + command + BEOPLAY_URL_RELEASE, {})

    async def async_digits(self, digit : str):
        """
        Send a digit keypress to the device. Digits are 0-9  

        """
        if (digit not in BEOPLAY_DIGITS):
            return
        await self.async_postReq("POST", BEOPLAY_DIGITS_URL, {BEOPLAY_DIGITS_KEY: int(digit)})


    ###############################################################
    # REQUESTS (BLOCKING) NETWORK CALLS
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

    def _postReq(self, type, path, data: dict = {}):
        try:
            r = None
            if self._connfail:
                LOG.debug("Connfail: %i", self._connfail)
                self._connfail -= 1
                return False
            if type == "PUT":
                r = requests.put(
                    BASE_URL.format(self._host, path),
                    json=data,
                    timeout=TIMEOUT,
                )
            elif type == "POST":
                if data is None or data == "":
                    r = requests.post(
                        BASE_URL.format(self._host, path), timeout=TIMEOUT
                    )
                else:
                    r = requests.post(
                        BASE_URL.format(self._host, path),
                        json=data,
                        timeout=TIMEOUT,
                    )
            elif type == "DELETE":
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
    # GET ATTRIBUTES FROM THE SPEAKER - BLOCKING CALLS
    ###############################################################

    # edited to only include in Use sources
    def getSources(self):
        r = self._getReq(BEOPLAY_URL_GET_SOURCES)
        if r:
            for elements in r:
                i = 0
                while i < len(r[elements]):
                    if r[elements][i][1]["inUse"] == True:
                        self.sourcesBorrowed.append(r[elements][i][1]["borrowed"])
                        self.sources.append(r[elements][i][1]["friendlyName"])
                        self.sourcesID.append(r[elements][i][0])
                    i += 1

    def getSource(self):
        self.source = None
        r = self._getReq(BEOPLAY_URL_ACTIVE_SOURCES)
        if r:
            self.source = r["primaryExperience"]["source"]["friendlyName"] if "friendlyName" in r["primaryExperience"]["source"] else None
            self.listeners = [listener["jid"] for listener in r["primaryExperience"]["listenerList"]["listener"]] if "listenerList" in r["primaryExperience"] else []
        return self.source

    def getStandby(self):
        r = self._getReq(BEOPLAY_URL_STANDBY)
        if r:
            if r["standby"]["powerState"] == "on":
                self.on = True
            else:
                self.on = False

    def getSoundMode(self):
        """ Get sound mode. Return the current active sound mode or None if not retreived."""
        self._soundMode = None
        self.getSoundModes()
        return self._soundMode

    def getSoundModes(self):
        """ Get sound modes. You need to call this before reading soundMode or soundModes."""
        r = self._getReq(BEOPLAY_URL_GET_SOUND_MODE)
        if r:
            r = r.get("mode", {"list": []})
            l = r.get("list", [])
            a = r.get("active", None)
            for element in l:
                self._soundModes[element["friendlyName"]] = element["id"]
                if a and a == element["id"]:
                    self._soundMode = element["friendlyName"]
            return self._soundModes
        return None

    def getStandPosition(self):
        self._standPosition = None
        r = self._getReq(BEOPLAY_URL_STAND_ACTIVE)
        if r and "active" in r:
            if r["active"] is not None:
                self._standPosition = r["active"] 
            return self._standPosition
        return None

    def getStandPositions(self):
        self._standPositions = {}
        r = self._getReq(BEOPLAY_URL_STAND)
        if r and "stand" in r:
            if r["stand"] is not None:
                for elements in r["stand"]["list"]:
                    self._standPositions[elements["friendlyName"]] = elements["id"]
                return self._standPositions
        return

    def getDeviceInfo(self):
        r = self._getReq("BeoDevice")
        if r:
            self._serialNumber = r["beoDevice"]["productId"]["serialNumber"]
            self._name = r["beoDevice"]["productFriendlyName"]["productFriendlyName"]
            self._typeNumber = r["beoDevice"]["productId"]["typeNumber"]
            self._itemNumber = r["beoDevice"]["productId"]["itemNumber"]
            self._softwareVersion = r["beoDevice"]["software"]["version"]
            self._hardwareVersion = r["beoDevice"]["hardware"]["version"]
            self._typeName = r["beoDevice"]["productId"]["productType"]
    ###############################################################
    # COMMANDS - Blocking
    ###############################################################

    def setVolume(self, volume):
        self.volume = volume
        volume = int(volume * 100)
        self._postReq("PUT", BEOPLAY_URL_SET_VOLUME, {"level": volume})

    def setMute(self, mute):
        if mute:
            self._postReq("PUT", BEOPLAY_URL_MUTE, {"muted": True})
        else:
            self._postReq("PUT", BEOPLAY_URL_MUTE, {"muted": False})

    def Play(self):
        self._postReq("POST", BEOPLAY_URL_PLAY, {})

    def Pause(self):
        self._postReq("POST", BEOPLAY_URL_PAUSE, {})

    def Stop(self):
        self._postReq("POST", BEOPLAY_URL_STOP, {})

    def StepUp(self):
        self._postReq("POST", BEOPLAY_URL_STEPUP, {})

    def StepDown(self):
        self._postReq("POST", BEOPLAY_URL_STEPDOWN, {})

    def Forward(self):
        self._postReq("POST", BEOPLAY_URL_FORWARD, {})

    def Backward(self):
        self._postReq("POST", BEOPLAY_URL_BACKWARD, {})

    def Repeat(self):
        self._postReq("POST", BEOPLAY_URL_REPEAT, {})

    def Shuffle(self):
        self._postReq("POST", BEOPLAY_URL_SHUFFLE, {})

    def Standby(self):
        self._postReq(
            "PUT", BEOPLAY_URL_STANDBY, {"standby": {"powerState": "standby"}}
        )
        self.on = False

    def turnOn(self):
        """Turn on the device. There is no such thing as an "on" command on B&O 
        equipment, so just select the first source, if it exists."""
        if len(self.sources)>0:
            self.setSource(self.sources[0])
            self.on = True

    def setSource(self, source):
        i = 0
        while i < len(self.sources):
            if self.sources[i] == source:
                chosenSource = self.sourcesID[i]
                self._postReq(
                    "POST",
                    BEOPLAY_URL_ACTIVE_SOURCES,
                    {"primaryExperience": {"source": {"id": chosenSource}}},
                )
            i += 1

    def setSoundMode(self, soundMode):
        """Get sound modes if not already done."""
        if not self._soundModes:
            self.getSoundModes()
        
        if soundMode not in self._soundModes:
            raise ValueError("Sound mode not available")
        
        soundModeId = self._soundModes[soundMode]
        
        self._postReq("PUT", BEOPLAY_URL_SET_SOUND_MODE, {"active": soundModeId})

    def setStandPosition(self, standPosition):
        """Get sound modes if not already done."""
        if not self._standPositions:
            self.getStandPositions()
        
        if standPosition not in self._standPositions:
            raise ValueError("Stand position not available")

        standPositionID = self._standPositions.get(standPosition)

        self._postReq("PUT", BEOPLAY_URL_STAND_ACTIVE, {"active": standPositionID})

    def joinExperience(self):
        self._postReq("POST", BEOPLAY_URL_JOIN_EXPERIENCE, {})

    def leaveExperience(self):
        self._postReq("DELETE", BEOPLAY_URL_LEAVE_EXPERIENCE, {})

    def playQueueItem(self, instantplay: bool, queueItem: dict):
        if instantplay:
            self._postReq(
                "POST", BEOPLAY_URL_PLAYQUEUE + BEOPLAY_URL_PLAYQUEUE_INSTANT, queueItem
            )
        else:
            self._postReq("POST", BEOPLAY_URL_PLAYQUEUE, queueItem)

    ###############################################################
    # PARSE NOTIFICATIONS MESSAGES
    ###############################################################

    def _processVolume(self, data):
        if (
            data["notification"]["type"] == "VOLUME"
            and data["notification"]["data"] is not None
        ):
            self.volume = int(data["notification"]["data"]["speaker"]["level"]) / 100
            self.min_volume = (
                int(data["notification"]["data"]["speaker"]["range"]["minimum"]) / 100
            )
            self.max_volume = (
                int(data["notification"]["data"]["speaker"]["range"]["maximum"]) / 100
            )
            self.muted = data["notification"]["data"]["speaker"]["muted"]

    def _processSource(self, data):
        if (
            data["notification"]["type"] == "SOURCE"
            and data["notification"]["data"] is not None
        ):
            if not data["notification"]["data"]:
                self.source = None
                self.state = None
                self.on = False
            else:
                self.source = data["notification"]["data"]["primaryExperience"][
                    "source"
                ]["friendlyName"]
                self.state = data["notification"]["data"]["primaryExperience"]["state"]
                self.on = True
            self.media_url = None
            self.media_track = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None

#    def _processPrimaryExperience(self, data):
#        if data["notification"]["type"] == "SOURCE":
#            self.primary_experience = data["primary"]

    def _processSourceExperienceChanged(self, data):
        if data["notification"]["type"] == "SOURCE_EXPERIENCE_CHANGED":
            self.listeners = data["notification"]["data"]["primaryExperience"]["listener"]

    def _processState(self, data):
        """Progress information provides info about the current state of play. 
        It is only reliable if the device is on. """
        if (
            data["notification"]["type"] == "PROGRESS_INFORMATION"
            and data["notification"]["data"] is not None
        ):
            self.state = data["notification"]["data"]["state"]
#            self.on = True

    def _processMusicInfo(self, data):
        if data["notification"]["type"] == "NOW_PLAYING_STORED_MUSIC":
            if data["notification"]["data"]["trackImage"]:
                self.media_url = data["notification"]["data"]["trackImage"][0]["url"]
            else:
                self.media_url = None
            self.media_artist = data["notification"]["data"]["artist"]
            self.media_album = data["notification"]["data"]["album"]
            self.media_track = data["notification"]["data"]["name"]
            self.media_genre = data["notification"]["data"]["genre"]
            self.media_country = None
            self.media_languages = None

        elif data["notification"]["type"] == "NOW_PLAYING_STORED_VIDEO":     
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_track = data["notification"]["data"]["name"]
            self.media_genre = None
            self.media_country = None
            self.media_languages = None

        elif data["notification"]["type"] == "NOW_PLAYING_NET_RADIO":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            if (
                "image" in data["notification"]["data"]
                and data["notification"]["data"]["image"]
            ):
                self.media_url = data["notification"]["data"]["image"][0]["url"]
                self.media_url = self.media_url.replace(
                    ".:8080/", ":8080/"
                )  # some B&O devices provide a hostname with trailing '.' which doesn't resolve
            if "name" in data["notification"]["data"]:
                self.media_artist = data["notification"]["data"]["name"]
            if "liveDescription" in data["notification"]["data"]:
                self.media_track = data["notification"]["data"]["liveDescription"]
            if "genre" in data["notification"]["data"]:
                self.media_genre = data["notification"]["data"]["genre"]
            if "country" in data["notification"]["data"]:
                self.media_country = data["notification"]["data"]["country"]
            if "languages" in data["notification"]["data"]["languages"]:
                self.media_languages = data["notification"]["data"]["languages"]

        elif data["notification"]["type"] == "NOW_PLAYING_LEGACY":
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

        elif data["notification"]["type"] == "NOW_PLAYING_ENDED":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            self.media_track = None

        elif data["notification"]["type"] == "NUMBER_AND_NAME":
            self.media_url = None
            self.media_artist = None
            self.media_album = None
            self.media_genre = None
            self.media_country = None
            self.media_languages = None
            self.media_track = (
                str(data["notification"]["data"]["number"])
                + ". "
                + data["notification"]["data"]["name"]
            )

    def _processSoundMode(self, data):
        if data["notification"]["type"] == "SOUND_ACTIVE_MODE_CHANGED":
            self._soundMode = data["notification"]["data"]["friendlyName"]


    def _processNotification(self, data):
        """Cumulative process all the potential notification information."""
        try:
            # get volume
            self._processVolume(data)
            # get source
            self._processSource(data)
            # get source experience
            self._processSourceExperienceChanged(data)
            # get state
            self._processState(data)
            # get currently playing music info
            self._processMusicInfo(data)
            # get sound mode
            self._processSoundMode(data)
        except KeyError:
            LOG.debug("Malformed notification: %s", str(data))
