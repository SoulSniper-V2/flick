# flick

Clef or Jev pick each tap on a real iPhone. The agent does not guess coordinates, and it does not take a photo per step.

Install the skill:

```bash
npx skills add SoulSniper-V2/flick -g -y
```

Clone the tools:

```bash
gh repo clone SoulSniper-V2/flick ~/Projects/flick
```

The skill tells the agent to install [iphone-use](https://github.com/leeguooooo/iphone-use), ask for `JEV_KEY` and the Cloudflare token, and run a goal. Keys stay in the environment.

```bash
python3 -m flick status
python3 -m flick goal "On X, open Theo's post about the T3 Code /goal flow and show the comments. Do not like, follow, or reply."
```

A step is one decision call, about 200 ms, plus the phone. Send, like, follow, and reply are refused before the tap.

Jev reads an image only if the request sends `TypeSafe-Danger-Zone-Images: true` and an `assets` map. Text from the accessibility tree is the fast path. The image path is the fallback when a control has no label.

The runner starts from a Mac. It is not an on-phone app you prompt with the cable out. That is a separate install and it is not this repo.
