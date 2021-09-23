#
# BeoPlay JSON interface for Bang & Olufsen Speakers, TVs and other NL devices
# Reference: https://documenter.getpostman.com/view/1053298/T1LTe4Lt#intro
# Reference: https://raw.githubusercontent.com/PolyPv/BeoRemote/master/BeoRemote.txt
# Lifted a lot of code from marton borzak's ha-beoplay
#

import requests
import json
import logging

LOG = logging.getLogger(__name__)
BASE_URL = 'http://{0}:8080/{1}'
TIMEOUT = 5.0
CONNFAILCOUNT = 5

class BeoPlay(object):
    def __init__(self, host, type='default'):
        self._host = host
        self._host_notifications = BASE_URL.format(self._host, 'BeoNotify/Notifications')
        self._name = None
        self._connfail = 0
        self.on = None
        self.min_volume = None
        self.max_volume = None
        self.volume = None
        self.muted = None
        self.source = None
        self.sources = []
        self.sourcesID = []
        self.sourcesBorrowed = []
        self.state = None
        self.media_url = None
        self.media_track = None
        self.media_artist = None
        self.media_album = None
        self.primary_experience = None
        self._serialNumber = None
        self._typeNumber = None
        self._itemNumber = None
        self._standPosition = None
        self.standPositions = []
        self.standPositionsID = []


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
        if data["notification"]["type"] == "VOLUME" and data["notification"]["data"]:
            self.volume = int(data["notification"]["data"]["speaker"]["level"])/100
            self.min_volume = int(data["notification"]["data"]["speaker"]["range"]["minimum"])/100
            self.max_volume = int(data["notification"]["data"]["speaker"]["range"]["maximum"])/100
            self.muted = data["notification"]["data"]["speaker"]["muted"]

    def getSource(self, data):
        if data["notification"]["type"] == "SOURCE" and data["notification"]["data"]:
            self.source = data["notification"]["data"]["primaryExperience"]["source"]["friendlyName"]
            self.on = True
            self.media_url = None
            self.media_track = None
            self.media_artist = None
            self.media_album = None

    def getPrimaryExperience(self, data):
        if data["notification"]["type"] == "SOURCE":
            self.primary_experience = data["primary"]

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

    def getState(self, data):
        if data["notification"]["type"] == "PROGRESS_INFORMATION" and data["notification"]["data"]:
            self.state = data["notification"]["data"]["state"]
            self.on = True

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

    def getMusicInfo(self, data):
        if data["notification"]["type"] == "NOW_PLAYING_STORED_MUSIC":
            if data["notification"]["data"]["trackImage"]:
                self.media_url = data["notification"]["data"]["trackImage"][0]["url"]
            else:
                self.media_url = None
            self.media_artist = data["notification"]["data"]["artist"]
            self.media_album = data["notification"]["data"]["album"]
            self.media_track = data["notification"]["data"]["name"]

        if data["notification"]["type"] == "NOW_PLAYING_NET_RADIO":
            if data["notification"]["data"]["image"]:
                self.media_url = data["notification"]["data"]["image"][0]["url"]
            else:
                self.media_url = None
            self.media_artist = data["notification"]["data"]["name"]
            self.media_album = None
            if 'liveDescription' in data["notification"]["data"]:
                self.media_track = data["notification"]["data"]["liveDescription"]
            else:
                self.media_track = None

        if data["notification"]["type"] == "NOW_PLAYING_LEGACY":
            self.media_url = None
            self.media_artist = None 
            self.media_album = None
            self.media_track = str(data["notification"]["data"]["trackNumber"])

        if data["notification"]["type"] == "NUMBER_AND_NAME":
            self.media_url = None
            self.media_artist = None 
            self.media_album = None
            self.media_track = str(data["notification"]["data"]["number"]) + ". " + data["notification"]["data"]["name"]
    
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
        self._postReq('PUT','BeoZone/Zone/Sound/Volume/Speaker/Level', {'level':volume})

    def setMute(self, mute):
        if mute:
            self._postReq('PUT','BeoZone/Zone/Sound/Volume/Speaker/Muted', {"muted":True})
        else:
            self._postReq('PUT','BeoZone/Zone/Sound/Volume/Speaker/Muted', {"muted":False})

    def Play(self):
        self._postReq('POST','BeoZone/Zone/Stream/Play','')
        self._postReq('POST','BeoZone/Zone/Stream/Play/Release','')

    def Pause(self):
        self._postReq('POST','BeoZone/Zone/Stream/Pause','')
        self._postReq('POST','BeoZone/Zone/Stream/Pause/Release','')

    def Stop(self):
        self._postReq('POST','BeoZone/Zone/Stream/Stop','')
        self._postReq('POST','BeoZone/Zone/Stream/Stop/Release','')

    def Next(self):
        self._postReq('POST','BeoZone/Zone/Stream/Forward','')
        self._postReq('POST','BeoZone/Zone/Stream/Forward/Release','')

    def Prev(self):
        self._postReq('POST','BeoZone/Zone/Stream/Backward','')
        self._postReq('POST','BeoZone/Zone/Stream/Backward/Release','')

    def Standby(self):
        self._postReq('PUT','BeoDevice/powerManagement/standby', {"standby":{"powerState":"standby"}})
        self.on = False

    def turnOn(self):
        self._postReq('PUT','BeoDevice/powerManagement/standby', {"standby":{"powerState":"on"}})
        self.on = True

    def setSource(self, source):
        i = 0
        while i < len(self.sources):
            if self.sources[i] == source:
                chosenSource = self.sourcesID[i]
                self._postReq('POST','BeoZone/Zone/ActiveSources', {"primaryExperience":{"source":{"id":chosenSource}}})
            i += 1

    def setStandPosition(self, standPosition):
        i = 0
        while i < len(self.standPositions):
            if self.standPositions[i] == standPosition:
                chosenStandPosition = self.standPositionsID[i]
                self._postReq('PUT','BeoZone/Zone/Stand/Active', {"active":chosenStandPosition})
            i += 1

    def joinExperience(self):
        self._postReq('POST','BeoZone/Zone/Device/OneWayJoin','')

    def leaveExperience(self):
        self._postReq('DELETE','BeoZone/Zone/ActiveSources/primaryExperience', '')

    def playQueueItem(self, instantplay: bool, queueItem: dict):
        if instantplay:
            self._postReq('POST','BeoZone/Zone/PlayQueue?instantplay',queueItem)
        else:
            self._postReq('POST','BeoZone/Zone/PlayQueue',queueItem)


if __name__ == '__main__':
    import sys
    ch = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.DEBUG)
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)

    if len(sys.argv) < 2:
        quit()

    gateway = BeoPlay(sys.argv[1])

    gateway.getDeviceInfo()
    print ("Serial Number: " , gateway._serialNumber)
    print ("Type Number: ", gateway._typeNumber)
    print ("Item Number: ",gateway._itemNumber)
    print ("Name: ",gateway._name)
    

    gateway.getSources()
    print (gateway.sources)
    print (gateway.sourcesID)
    print (gateway.sourcesBorrowed)
    
    gateway.getStandPositions()
    print (gateway.standPositions)
    print (gateway.standPositionsID)

    gateway.getStandPosition()
    print ("Stand Position: ", gateway._standPosition)

    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "impulsive","track": {"deezer": { "id": 997764 }, "image" : []}}})
    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "planned","station": {"tuneIn": {"stationId": "s45455"}, "image" : []}}})

