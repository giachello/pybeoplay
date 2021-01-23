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
        self.state = None
        self.media_url = None
        self.media_track = None
        self.media_artist = None
        self.media_album = None
        self.primary_experience = None
        self._serialNumber = None
        self._typeNumber = None
        self._itemNumber = None

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
                        if r[elements][i][1]["borrowed"] == True:
                            self.sources.append("\U0001F517 " + r[elements][i][1]["friendlyName"])
                        else:
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

    def getMusicInfo(self, data):
        if data["notification"]["type"] == "NOW_PLAYING_STORED_MUSIC" and data["notification"]["data"]["trackImage"]:
            self.media_url = data["notification"]["data"]["trackImage"][0]["url"]
            self.media_artist = data["notification"]["data"]["artist"]
            self.media_track = data["notification"]["data"]["name"]
            self.media_album = data["notification"]["data"]["album"]

        if data["notification"]["type"] == "NOW_PLAYING_NET_RADIO":
            self.media_artist = data["notification"]["data"]["name"]
            if data["notification"]["data"]["image"]:
                self.media_url = data["notification"]["data"]["image"][0]["url"]
            if 'liveDescription' in data["notification"]["data"]:
                self.media_track = data["notification"]["data"]["liveDescription"]
    
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

    def joinExperience(self):
        self._postReq('POST','BeoZone/Zone/Device/OneWayJoin','')

    def leaveExperience(self):
        self._postReq('DELETE','BeoZone/Zone/ActiveSources/primaryExperience', '')


if __name__ == '__main__':
    import sys
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    LOG.addHandler(ch)

    if len(sys.argv) < 2:
        quit()

    gateway = BeoPlay(sys.argv[1])
    gateway.getSources()
    print (gateway.sources)

