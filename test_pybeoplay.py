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
    print ("Serial Number: " , gateway.serialNumber)
    print ("Type Number: ", gateway.typeNumber)
    print ("Item Number: ",gateway.itemNumber)
    print ("Type Name: ",gateway.typeName)
    print ("SW: ",gateway.softwareVersion)
    print ("HW: ",gateway.hardwareVersion)
    print ("Name: ",gateway.name)
    print ("Standby: ", gateway.on)
    
    print ("--- SOURCES ---")
    gateway.getSources()
    print (gateway.sources)
    print (gateway.sourcesID)
    print (gateway.sourcesBorrowed)
    gateway.getSource()
    print ("Active source: ", gateway.source)
    
    print ("--- STAND POSITIONS ---")
    gateway.getStandPositions()
    print (gateway.standPositions)
    print (gateway.standPositionsID)

    gateway.getStandPosition()
    print ("Stand Position: ", gateway.standPosition)

    print ("--- SOUND MODES ---")
    gateway.getSoundMode()
    print("Sound Mode: ", gateway.soundMode)
    gateway.getSoundModes()
    print (gateway.soundModes)
    print (gateway.soundModesID)
    print("Sound Mode: ", gateway.soundMode)
    gateway.getSoundMode()
    print("Sound Mode: ", gateway.soundMode)

    gateway.getStandby()
    print ("On State: ", gateway.on)


#    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "impulsive","track": {"deezer": { "id": 997764 }, "image" : []}}})
#    gateway.playQueueItem(True, {"playQueueItem": {"behaviour": "planned","station": {"tuneIn": {"stationId": "s45455"}, "image" : []}}})
    gateway.playQueueItem(True,{
        "playQueueItem": 
            {
                "behaviour": "impulsive",
                "track": {
                    "dlna": {
                        "url": "http://192.168.1.217:50002/v/NDLNA/785.mp4"
                    }}}}
    )
    