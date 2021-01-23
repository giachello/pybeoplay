# ha-beoplay 

Beoplay python wrapper to integrate B&amp;O speakers/TVs to Python

API wrapped to an object that can be used with to read the state and control BeoPlay devices.

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

The following commands are avialable:
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
