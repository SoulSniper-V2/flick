# flick

An agent opens apps on a real iPhone and prints the time. No screenshot per tap.

The phone already has a [iphone-use](https://github.com/leeguooooo/iphone-use) runner on it. flick talks to that daemon, launches by name, reads the accessibility tree, and goes home. A settled open is a few hundred milliseconds. A photo is never taken.

## Demo

Phone unlocked, cable in, runner awake.

```bash
python3 -m flick status
python3 -m flick demo
```

`demo` opens Weather, Clock, and Calendar, checks each one actually came up, then presses Home. It prints launch time, tree time, and the total. `photos` is 0.

On an iPhone 17 running iOS 27, with the runner already awake, that demo finished in 3.2 seconds. Weather 0.5s, Clock 0.6s, Calendar 1.6s, Home 0.5s. Zero photos.

That is the clip. Terminal on one side, phone on the other. Three apps, no vision model, no coordinate guess.

## What is not in this cut

The runner still starts from a Mac. After the first USB setup it can stay on Wi-Fi until the phone reboots, locks, or the signing lease ends. Pulling the cable is not the same as deleting the Mac.

An app installed from the Mac that then drives the phone with no Mac in the room is a different program. It has to be the test runner and the client in one process, on the phone, talking to `testmanagerd` through a loopback. [TouchSynthesis](https://github.com/willfaust/TouchSynthesis) is that program. It is iOS 26, needs a pairing record, a loopback VPN, and a passcode prompt, and it speaks pixels, not labels. It is the unplugged path. It is not this demo.

## Commands

| Command | Does |
|---|---|
| `status` | Is the phone drivable? |
| `see` | Short labels on the current screen. Long text is dropped. |
| `demo` | Weather, Clock, Calendar, Home. Times only. |
