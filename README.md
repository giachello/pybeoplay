# Bang & Olufsen BeoPlay devices Python integration module

Beoplay Python wrapper to integrate B&amp;O speakers/TVs to Python that use the BeoPlay API. BeoPlay API is the 2nd generation B&O API, after [Masterlink Gateway](https://github.com/giachello/mlgw) and before [Mozart](https://github.com/bang-olufsen/mozart-open-api). It is supported by devices built from the early 2000s to the late 2010s, including several BeoVision TV, BeoLab speakers and the NL/ML Converter.

The API is wrapped in an object that can be used  to read the state and control BeoPlay devices. It includes both methods for blocking calls, and async calls with callbacks using aiohttp.

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
- set source
- join experience
- leave experience
- play queue item
- set stand position
