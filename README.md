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

The following key presses are available:
```Cursor/Select, Cursor/Up, Cursor/Down, Cursor/Left, Cursor/Right, Cursor/Exit, Cursor/Back, Cursor/PageUp, Cursor/PageDown, Cursor/Clear, Stream/Play, Stream/Stop, Stream/Pause, Stream/Wind, Stream/Rewind, Stream/Forward, Stream/Backward, List/StepUp, List/StepDown, List/PreviousElement, List/Shuffle, List/Repeat, Menu/Root, Menu/Option, Menu/Setup, Menu/Contents, Menu/Favorites, Menu/ElectronicProgramGuide, Menu/VideoOnDemand, Menu/Text, Menu/HbbTV,Menu/HomeControl, Device/Information, Device/Eject, Device/TogglePower, Device/Languages, Device/Subtitles, Device/OneWayJoin, Device/Mots, Record/Record, Generic/Blue, Generic/Red, Generic/Green, Generic/Yellow,``` and the digits ```0-9```

