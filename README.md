# GeekMagicWeatherClockAPI

A Python wrapper for controlling the **GeekMagic SmallTV** over your local network. Supports uploading images/GIFs, switching themes, adjusting brightness, and managing files on the device.

[PyPI](https://pypi.org/project/GeekMagicWeatherClockAPI/)

---

## Installation

```bash
pip install GeekMagicWeatherClockAPI
```

## Requirements

- Python 3.10+
- [`requests`](https://pypi.org/project/requests/) (installed automatically)

---

## Setup

Find your SmallTV's local IP address (check your router's device list or the SmallTV's settings menu), then:

```python
from GeekMagicWeatherClockAPI import SmallTV

tv = SmallTV("192.168.1.85")
```

A persistent HTTP session is created automatically. All requests reuse this session, so there's no need to manage connections manually.

---

## Return values

Every method returns the same dictionary — no exceptions are raised for network or validation errors:

```python
{
    "success":     bool,       # True if the device responded successfully
    "status_code": int | None, # HTTP status code, or None if the request never completed
    "response":    str | None, # Raw response body from the device
    "error":       str | None, # Human-readable error message on failure, else None
}
```

### Checking results

```python
result = tv.set_brightness(50)

if result["success"]:
    print("Done!")
else:
    print("Something went wrong:", result["error"])
```

---

## Usage

### Upload an image

```python
tv.upload("my_animation.gif")

# Increase retries for flaky firmware responses
tv.upload("my_animation.gif", retries=5)
```

### Display an image

```python
tv.set_image("my_animation.gif")
```

### Upload and immediately display

```python
tv.upload_and_set("my_animation.gif")
```

### Replace an image

Deletes the old file, uploads the new one, and displays it — all in one call.

```python
tv.replace("old_animation.gif", "new_animation.gif")
```

### Delete an image

```python
tv.delete("my_animation.gif")
```

### Set brightness

Accepts a value from `0` to `100`.

```python
tv.set_brightness(75)
```

### Set theme

Accepts either an integer (`1`–`7`) or the theme name as a string (case-insensitive).

```python
tv.set_theme(3)
tv.set_theme("Photo Album")
```

| ID | Theme Name           |
|----|----------------------|
| 1  | Weather Clock Today  |
| 2  | Weather Forecast     |
| 3  | Photo Album          |
| 4  | Time Style 1         |
| 5  | Time Style 2         |
| 6  | Time Style 3         |
| 7  | Simple Weather Clock |

---

## Examples

### Basic setup and display

```python
from GeekMagicWeatherClockAPI import SmallTV

tv = SmallTV("192.168.1.85")

tv.upload_and_set("spaceman.gif")
tv.set_brightness(30)
tv.set_theme("Weather Clock Today")
```

### Checking every result

```python
tv = SmallTV("192.168.1.85")

for step, result in [
    ("upload",     tv.upload("clock.gif")),
    ("display",    tv.set_image("clock.gif")),
    ("brightness", tv.set_brightness(60)),
    ("theme",      tv.set_theme(1)),
]:
    status = "OK" if result["success"] else f"FAILED — {result['error']}"
    print(f"{step:12} {status}")
```

### Batch upload a folder of GIFs

```python
from pathlib import Path

tv = SmallTV("192.168.1.85")

gifs = list(Path("./animations").glob("*.gif"))

for gif in gifs:
    result = tv.upload(gif)
    if result["success"]:
        print(f"Uploaded: {gif.name}")
    else:
        print(f"Failed:   {gif.name} — {result['error']}")
```

### Rotate through themes on a schedule

```python
import time

tv = SmallTV("192.168.1.85")

themes = list(tv.THEMES.keys())  # [1, 2, 3, 4, 5, 6, 7]

for theme_id in themes:
    result = tv.set_theme(theme_id)
    if result["success"]:
        print(f"Now showing: {tv.THEMES[theme_id]}")
    time.sleep(10)
```

### Night mode — dim at a set hour

```python
from datetime import datetime

tv = SmallTV("192.168.1.85")

hour = datetime.now().hour
brightness = 10 if 22 <= hour or hour < 7 else 80

result = tv.set_brightness(brightness)
print(f"Brightness set to {brightness}" if result["success"] else result["error"])
```

### Upload with retry and graceful fallback

```python
tv = SmallTV("192.168.1.85")

result = tv.upload("hero.gif", retries=5)

if result["success"]:
    tv.set_image("hero.gif")
else:
    print("Upload failed after all retries:", result["error"])
    # Fall back to a theme instead
    tv.set_theme("Weather Clock Today")
```

### Swap a live image safely

```python
tv = SmallTV("192.168.1.85")

# Removes "old.gif", uploads "new.gif", and displays it
result = tv.replace("old.gif", "new.gif")

if not result["success"]:
    print("Replace failed:", result["error"])
```

---

## Notes

- The SmallTV firmware occasionally returns malformed `Content-Length` headers on upload responses. The `upload` method automatically retries and cleans up partial uploads when this happens.
- All methods return a structured dict and never raise — check `result["success"]` instead of wrapping calls in `try/except`.
- File management methods operate on the `/image/` directory on the device.
- The `THEMES` dict is a public class attribute and can be read directly to enumerate valid theme names: `SmallTV.THEMES`.

---

> **Dev note:** on release, bump the version in `pyproject.toml` and run `python -m build` then `twine upload dist/*`.