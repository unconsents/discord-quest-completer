# Discord Quest Completer

> Automated Discord quest completion with multi-account support, auto-enrollment, and a clean live-updating progress display.

---

## Features

- **Auto-enrollment** — Automatically accepts all available quests, no manual clicking required
- **Multi-token support** — Run as many accounts as you want simultaneously, each with its own colored tag
- **Concurrent quest completion** — All quests on each account run at the same time, not one by one
- **Live progress list** — One row per quest that updates in place, and only redraws when a quest's progress or status actually changes
- **Purple Eclipse theme** — Truecolor gradient banner and progress bars, with a centered header
- **Automatic dependency setup** — Missing packages are installed on first run, and a conflicting `discord.py` install is removed for you
- **Invalid token handling** — Bad tokens are detected on login and automatically removed from `tokens.txt`
- **Failure protection** — A quest is aborted after 5 consecutive failed requests instead of retrying forever
- **Supported quest types:**
  - `WATCH_VIDEO` / `WATCH_VIDEO_ON_MOBILE`
  - `PLAY_ON_DESKTOP`
  - `STREAM_ON_DESKTOP`
  - `PLAY_ACTIVITY`
- **Multi-task quests** — Quests that require all of their tasks (`and`) are handled, not just quests that need any one (`or`)

---

## Requirements

- Python 3.10 or newer
- A terminal with truecolor support (Windows Terminal, VS Code terminal, and most modern terminals)
- A terminal at least ~115 columns wide for the full progress list. Narrower windows crop the right-hand columns.

The script installs these automatically if they are missing, so you can skip the manual install if you prefer:

```
aiohttp
colour
discord.py-self
```

> **Note:** `discord.py` and `discord.py-self` both provide the `discord` module and conflict with each other. If `discord.py` is installed, the script uninstalls it, tells you why, and reinstalls `discord.py-self`. Don't use this script in an environment where you need the regular `discord.py`.

---

## Installation

```bash
git clone https://github.com/saint-tools/discord-quest-completer.git
cd discord-quest-completer
pip install -r requirements.txt (not required anymore since auto install)
```

Running `pip install -r requirements.txt` is optional. The script installs anything missing on first launch.

---

## Configuration

**`tokens.txt`** — one token per line:
```
token1
token2
token3
```

**`config.json`** — settings file in the same folder as `main.py`:
```json
{
    "timezone": "America/New_York",
    "locale": "en-US"
}
```

| Field | Description |
|---|---|
| `timezone` | Your timezone string, e.g. `"Europe/London"`. Defaults to `America/New_York`. |
| `locale` | Your locale string, e.g. `"en-GB"`. Defaults to `en-US`. |

---

## Usage

```bash
python main.py
```

The script will:
1. Check for required packages and install any that are missing
2. Log in all tokens from `tokens.txt`
3. Fetch all available quests for each account
4. Auto-enroll in any quests not yet accepted
5. Complete all eligible quests concurrently
6. Show a live progress row for each quest, ending in `done` or `failed`

### Claiming rewards

Rewards are **not** claimed automatically. Claiming can require a captcha, so when a quest shows `done`, open the Discord client and claim the reward there.

---

## Project Structure

```
.
├── main.py           # main script
├── tokens.txt        # one Discord token per line
├── config.json       # timezone and locale
├── requirements.txt  # pip dependencies
└── README.md
```

---

## Notes

- Enrollment can be blocked by Discord for a period of time. When that happens the script prints the time it unblocks and still runs any quests you are already enrolled in. Run it again after the block expires to pick up the rest.
- Quests that can't be completed automatically are skipped with a message: `PLAY_ON_XBOX`, `PLAY_ON_PLAYSTATION`, and achievement-based quests.
- Play, stream, and activity quests are progressed by sending heartbeats, which Discord's API only credits for desktop-client traffic. If progress doesn't advance, the server may be rejecting them.
- `STREAM_ON_DESKTOP` quests may require another person in the stream, as in the official client.
- Any quest that fails 5 requests in a row is aborted and its row is marked `failed`. Details are printed above the list.
- Avoid running too many tokens at once to stay within Discord rate limits.

---

## Disclaimer

This project is for educational purposes only. You are solely responsible for how you use this tool. Automating quests violates Discord's Terms of Service, and Discord has been reported to monitor for it and suspend quest access or accounts. Running many accounts at once raises that risk. The author assumes no liability for any consequences.

---

## License

MIT License
