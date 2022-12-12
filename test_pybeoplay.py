from pybeoplay import BeoPlay
import logging

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
    print ("Serial Number: " , gateway._serialNumber)
    print ("Type Number: ", gateway._typeNumber)
    print ("Item Number: ",gateway._itemNumber)
    print ("Name: ",gateway._name)
    print ("Standby: ", gateway.on)
    
    gateway.getSources()
    print (gateway.sources)
    print (gateway.sourcesID)
    print (gateway.sourcesBorrowed)
    
    gateway.getStandPositions()
    print (gateway.standPositions)
    print (gateway.standPositionsID)

    gateway.getStandPosition()
    print ("Stand Position: ", gateway.standPosition)

    gateway.getStandby()
    print ("On State: ", gateway.on)


    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "impulsive","track": {"deezer": { "id": 997764 }, "image" : []}}})
    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "planned","station": {"tuneIn": {"stationId": "s45455"}, "image" : []}}})
