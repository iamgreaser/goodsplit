Goodsplit is an autosplitter-first split timer for speedrunning.

Yep, that's right. Manually splitting is a second-class thing.

Because of that, you don't need to come up with your own splits or work out what you're going to do first. It'll add splits as you go along, and if you get two things mixed up it'll adapt on the fly.

# Games supported

## Linux only

* System Shock 2 (win32, uses inotify)

## Multiplatform

# TODOs

## Critical TODO

Once these are all done I'm putting a proper version on this.

* Compare past splits

## Cleanup TODO

* Don't instantly close everything when someone presses the X button on the root window
* Only update splits on GUI when they've changed
* Use argparse to parse arguments

## Other TODO

* Basic customisation
  * GUI themes
* Load removal (well, it's partially implemented)
* Log regex API
* Memory reading API (cross-platform)
* Plugins for games
* Visual autosplitting API (using OpenCV)
* Windows support

