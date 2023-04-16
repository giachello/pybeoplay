from pybeoplay import BeoPlay
import logging
import asyncio
import aiohttp

LOG = logging.getLogger(__name__)

async def test_volume(gateway : BeoPlay):
    await asyncio.sleep(10)
    await gateway.async_set_volume(0.40)
    await asyncio.sleep(4)
    await gateway.async_set_volume(0.37)

async def get_status(gateway : BeoPlay):
    while True:
        try:
            await asyncio.sleep(10)
            _on : bool = await gateway.async_get_standby()
            print("Status is on: ", str(_on))
        except Exception as e:
            LOG.info("Exception %s", str(e))

async def test_remote(gateway : BeoPlay):
    await gateway.async_turn_on()
    await asyncio.sleep(10)
    await gateway.async_remote_command('Cursor/Down')
    await asyncio.sleep(4)
    await gateway.async_remote_command('Stream/Play')

async def main(host):
    timeout = aiohttp.ClientTimeout(total=None, connect=None, sock_connect=None, sock_read=None)
    async with aiohttp.ClientSession(timeout = timeout) as session:
        gateway = BeoPlay(host, session)

        await gateway.async_get_device_info()
        print ("Serial Number: " , gateway.serialNumber)
        print ("Type Number: ", gateway.typeNumber)
        print ("Item Number: ",gateway.itemNumber)
        print ("Name: ",gateway.name)
        print ("Standby: ", gateway.on)

        sources = await gateway.async_get_sources()
        print ("Sources: ", sources)

        asyncio.create_task(test_remote(gateway))
        asyncio.create_task(test_volume(gateway))
        asyncio.create_task(get_status(gateway))

        def callback(json_data):
            print ("On State: " , gateway.on)
            print ("Source: ", gateway.source)
            print ("Min Volume: " , gateway.min_volume)
            print ("Max Volume: " , gateway.max_volume)
            print ("Volume: " , gateway.volume)
            print ("Muted: " , gateway.muted)
            print ("State: " , gateway.state)
            print ("Media URL: " , gateway.media_url)
            print ("Media track: " , gateway.media_track)
            print ("Media artist: " , gateway.media_artist)
            print ("Media album: " , gateway.media_album)
            print ("Media genre: " , gateway.media_genre)
            print ("Media country: " , gateway.media_country)
            print ("Media languages: " , gateway.media_languages)
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


