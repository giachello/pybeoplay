# pybeoplay 

Beoplay Python wrapper to integrate B&amp;O speakers/TVs to Python. This library provides both blocking calls through the requests module and async using asyncio aiohttp calls.

The API is wrapped in an object that can be used with to read the state and control BeoPlay devices. It includes both methods for blocking calls, and async calls with callbacks.

Reference information [is on this page.](https://documenter.getpostman.com/view/1053298/T1LTe4Lt)

Some more information on the Notifications stream is in the [EVENTS.md](EVENTS.md) file.

Currently gets the following attributes:
- volume
- mute
- source
- source list
- primary experience
- state
- standby
- track image (if available)
- artist 
- album
- song(name) (if available)
- description (if available)
- stand positions

The following commands are available:
- set volume
- set mute
- play
- pause
- stop
- next
- previous
- standby
- turn on
- set source
- join experience
- leave experience
- play queue item
- set stand position
