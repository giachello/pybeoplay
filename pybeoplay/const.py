#
# BeoPlay JSON interface for Bang & Olufsen Speakers, TVs and other NL devices
# Reference: https://documenter.getpostman.com/view/1053298/T1LTe4Lt#intro
# Reference: https://raw.githubusercontent.com/PolyPv/BeoRemote/master/BeoRemote.txt
# Lifted a lot of code from marton borzak's ha-beoplay
#
#
# pybeoplay constants
#


BASE_URL = 'http://{0}:8080/{1}'
TIMEOUT = 5.0
CONNFAILCOUNT = 5


BEOPLAY_URL_NOTIFICATIONS = 'BeoNotify/Notifications'
BEOPLAY_URL_SET_VOLUME = 'BeoZone/Zone/Sound/Volume/Speaker/Level'
BEOPLAY_URL_MUTE = 'BeoZone/Zone/Sound/Volume/Speaker/Muted'
BEOPLAY_URL_PLAY = 'BeoZone/Zone/Stream/Play'
BEOPLAY_URL_RELEASE = '/Release'
BEOPLAY_URL_PAUSE = 'BeoZone/Zone/Stream/Pause'
BEOPLAY_URL_STOP = 'BeoZone/Zone/Stream/Stop'
BEOPLAY_URL_FORWARD = 'BeoZone/Zone/Stream/Forward'
BEOPLAY_URL_BACKWARD = 'BeoZone/Zone/Stream/Backward'
BEOPLAY_URL_STANDBY = 'BeoDevice/powerManagement/standby'
BEOPLAY_URL_SET_SOURCE = 'BeoZone/Zone/ActiveSources'
BEOPLAY_URL_SET_STAND = 'BeoZone/Zone/Stand/Active'
BEOPLAY_URL_JOIN_EXPERIENCE = 'BeoZone/Zone/Device/OneWayJoin'
BEOPLAY_URL_LEAVE_EXPERIENCE = 'BeoZone/Zone/ActiveSources/primaryExperience'
BEOPLAY_URL_PLAYQUEUE = 'BeoZone/Zone/PlayQueue'
BEOPLAY_URL_PLAYQUEUE_INSTANT = '?instantplay'
