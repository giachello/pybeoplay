from pybeoplay import BeoPlay
import logging
import json
import requests

LOG = logging.getLogger(__name__)


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
    print ("Serial Number: " , gateway.serialNumber)
    print ("Type Number: ", gateway.typeNumber)
    print ("Item Number: ",gateway.itemNumber)
    print ("Name: ",gateway.name)
    print ("Standby: ", gateway.on)
    
    gateway.getStandby()
    print ("Standby: ", gateway.on)

    r = requests.get(gateway._host_notifications, stream=True)

    if r.encoding is None:
        r.encoding = 'utf-8'

    for line in r.iter_lines(decode_unicode=True):
        if line:
            json_line = json.loads(line)
            print(json_line)

            gateway._processNotification(json_line)
            print ("State: ", gateway.state)
            print ("Source: ", gateway.source)
            print ("Muted: ", gateway.muted)
            print ("Volume: ", gateway.volume)
            print ("Media Track: ", gateway.media_track)

