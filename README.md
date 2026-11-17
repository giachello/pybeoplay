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
- sound modes
- speaker groups / listeners

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
- set sound mode

On the remote functionality, the following key presses are available:

```Cursor/Select, Cursor/Up, Cursor/Down, Cursor/Left, Cursor/Right, Cursor/Exit, Cursor/Back, Cursor/PageUp, Cursor/PageDown, Cursor/Clear, Stream/Play, Stream/Stop, Stream/Pause, Stream/Wind, Stream/Rewind, Stream/Forward, Stream/Backward, List/StepUp, List/StepDown, List/PreviousElement, List/Shuffle, List/Repeat, Menu/Root, Menu/Option, Menu/Setup, Menu/Contents, Menu/Favorites, Menu/ElectronicProgramGuide, Menu/VideoOnDemand, Menu/Text, Menu/HbbTV,Menu/HomeControl, Device/Information, Device/Eject, Device/TogglePower, Device/Languages, Device/Subtitles, Device/OneWayJoin, Device/Mots, Record/Record, Generic/Blue, Generic/Red, Generic/Green, Generic/Yellow,``` 

The digits ```0-9```

And the following One Way commands (thanks to [@pieterhoekstra](https://github.com/pieterhoekstra) ) 
`CURSOR_UP, CURSOR_LEFT, CURSOR_RIGHT, CURSOR_DOWN, BACK, MENU, SELECT, STEP_UP, STEP_DOWN, VOLUME_UP, VOLUME_DOWN, REWIND, PLAY, WIND, STANDBY, RELEASE, PMUTE`.
Speaker groups (TV only) can be fetched and selected by friendly name:

```python
groups = device.getSpeakerGroups()  # {"Start-up": 0, "Cinema": 1, ...}
active = device.speakerGroup       # Active group name from the last fetch
device.setSpeakerGroup("Cinema")
active = device.getSpeakerGroup()  # Fetch the current active group name
```

The async equivalents are `async_get_speaker_groups()`,
`async_get_speaker_group()`, and `async_set_speaker_group(name)`.
`device.speakerGroups` contains the last fetched name-to-ID mapping. Selecting
an unknown name raises `ValueError`; selection fetches the groups first if the
cache is empty.

Expand the current experience to another device using its product JID:

```python
device.expand("2730.1200322.28760191@products.bang-olufsen.com")
# Or with an aiohttp session supplied to BeoPlay:
await device.async_expand("2730.1200322.28760191@products.bang-olufsen.com")
```

Selection and expand methods return whether the request succeeded. Fetching
speaker groups returns `None` if unavailable, or a dictionary (possibly empty).
