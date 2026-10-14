---
name: flick
description: Drive a real iPhone. Jev or Clef pick each tap from a closed list. Use when the user wants the phone controlled, this skill installed, or a goal run on the device.
---

# flick

You do not guess coordinates. You do not take a photo per tap. Jev picks the next action from the labels on screen. Clef is the fallback. Send, like, follow, reply, and pay are refused before the tap.

Repo: https://github.com/SoulSniper-V2/flick

## Install the skill

```bash
npx skills add SoulSniper-V2/flick -g -y
```

Then clone the tools. The skill file is instructions. The CLI and MCP live in the repo.

```bash
gh repo clone SoulSniper-V2/flick ~/Projects/flick
```

## Set up the phone

Do this on the Mac the iPhone is plugged into. Ask before installing. The phone must be unlocked, screen on, cable in.

1. If `iphone-use` is not on the PATH:

```bash
curl -fsSL https://raw.githubusercontent.com/leeguooooo/iphone-use/main/install.sh | bash
iphone-use doctor
iphone-use setup
```

2. Ask the person for these if they are not already exported. Never invent a key. Never write one into the repo. Never repeat a key back.

- `JEV_KEY` or `TYPESAFE_API_KEY`
- `CF_ACCOUNT`
- `CF_TOKEN` or `CLOUDFLARE_API_TOKEN`

3. Prove it:

```bash
cd ~/Projects/flick
python3 -m flick status
python3 -m flick bench
```

`status` must say drivable. `bench` must show Jev and the Clef models choosing `tap_theo` on a frozen screen. That bench does not touch the phone.

4. Tell the person to set Auto-Lock to Never while a run is live. A 30 second lock makes the runner refuse screen reads. The passcode cannot be entered from the Mac. If `status` says unlock in hand, stop and ask. Do not retry in a loop.

## Run a goal

```bash
python3 -m flick goal "On X, open Theo's post about the T3 Code /goal flow and show the comments."
```

MCP, if the host can load a stdio server:

```json
{
  "mcpServers": {
    "flick": {
      "command": "python3",
      "args": ["-m", "flick.mcp_server"],
      "cwd": "/Users/YOU/Projects/flick",
      "env": {
        "JEV_KEY": "${JEV_KEY}",
        "CF_ACCOUNT": "${CF_ACCOUNT}",
        "CF_TOKEN": "${CF_TOKEN}"
      }
    }
  }
}
```

Tools: `phone_status`, `phone_see`, `phone_goal`.

## How a step works

The tree comes back as short labels. Jev gets a closed list: launch X, type `t3.gg`, tap a ranked control, scroll, back, done. Compose, Follow, Like, and Reply are not in the list. A step is one model call, about 150 ms for Jev and 270 to 460 ms for the Clef models, plus the phone. Eight questions are not slower than one. Do not add a second call to be sure.

Jev can see a photo only with the header `TypeSafe-Danger-Zone-Images: true` and an `assets` map. Use that when a control has no label. Do not use it as the default. Clef-omni takes a JPEG in `images` without that header.

## Stop

Do not open Mail or Messages unless asked. Do not check out. Do not post. If the same action repeats twice, stop and read the screen. If the runner says the screen cannot be read, the phone is asleep or locked from the Mac's side even if it looks awake to the person. Ask them to tap the screen and leave it on.
