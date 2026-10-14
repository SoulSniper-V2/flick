---
name: flick
description: Drive a real iPhone from an agent. Clef or Jev pick each tap from the accessibility tree. Use when the user wants the phone controlled, a demo recorded, or this skill installed.
---

# flick

The phone is controlled by a closed decision, not by you guessing coordinates. Clef or Jev pick the next tap. You do not send, like, follow, reply, or pay.

## Install this skill

```bash
npx skills add SoulSniper-V2/flick -g -y
```

That clones nothing by itself. After the skill is installed, clone the repo the tools live in:

```bash
gh repo clone SoulSniper-V2/flick ~/Projects/flick
```

Repo: https://github.com/SoulSniper-V2/flick

## Set up the phone

Do this on the Mac the iPhone is plugged into. Ask the person before running the installer. Keep the phone unlocked.

1. If `iphone-use` is missing, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/leeguooooo/iphone-use/main/install.sh | bash
iphone-use doctor
iphone-use setup
```

2. Ask the person for three values if they are not already in the environment. Never invent them, never write them into the repo, never echo them back.

- `JEV_KEY` (or `TYPESAFE_API_KEY`)
- `CF_ACCOUNT`
- `CF_TOKEN` (or `CLOUDFLARE_API_TOKEN`)

3. Check the phone:

```bash
cd ~/Projects/flick
python3 -m flick status
```

`drivable` must be true. If it says parked, the person unlocks the phone and you run `iphone-use setup` again only if status stays down.

## Use it

MCP, for an agent that can load a stdio server:

```json
{
  "mcpServers": {
    "flick": {
      "command": "python3",
      "args": ["-m", "flick.mcp_server"],
      "cwd": "/Users/YOU/Projects/flick"
    }
  }
}
```

Tools: `phone_status`, `phone_see`, `phone_goal`.

Or from the terminal:

```bash
python3 -m flick goal "On X, open Theo's post about the T3 Code /goal flow and show the comments. Do not like, follow, or reply."
```

Each step is one Jev call (Clef-omni if Jev is unset). The model sees the short labels, not a photo, unless you later pass an image with `TypeSafe-Danger-Zone-Images: true`. A send, like, follow, or reply is refused in code before the tap.

## What this is not

This cut still needs the Mac daemon. After the first USB setup the runner can stay on Wi-Fi until reboot, lock, or the signing lease. An on-phone app you prompt with no Mac in the room is a different program and is not shipped here. Do not tell the person it is.

Do not open Mail or Messages unless they asked. Do not check out of a cart. Do not post.
