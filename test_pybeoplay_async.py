from pybeoplay import BeoPlay
import logging
import asyncio
import aiohttp

LOG = logging.getLogger(__name__)


async def main(host):
    async with aiohttp.ClientSession() as session:
        gateway = BeoPlay(host, session)
        
        await gateway.async_getDeviceInfo()
        print ("Serial Number: " , gateway._serialNumber)
        print ("Type Number: ", gateway._typeNumber)
        print ("Item Number: ",gateway._itemNumber)
        print ("Name: ",gateway._name)
        print ("Standby: ", gateway.on)
        
        def callback():
            print ("On State: " , gateway.on)
            print ("Min Volume: " , gateway.min_volume)
            print ("Max Volume: " , gateway.max_volume)
            print ("Volume: " , gateway.volume)
            print ("Muted: " , gateway.muted)
            print ("State: " , gateway.state)
            print ("Media URL: " , gateway.media_url)
            print ("Media track: " , gateway.media_track)
            print ("Media artist: " , gateway.media_artist)
            print ("Media album: " , gateway.media_album)
            print ("Primary experience: " , gateway.primary_experience)            

        r = await  gateway.async_notificationsTask(callback)
        print (str(r))




if __name__ == '__main__':
    import sys
    ch = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.DEBUG)
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)

    if len(sys.argv) < 2:
        quit()

    asyncio.run(main(sys.argv[1]))


