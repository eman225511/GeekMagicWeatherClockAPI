# GeekMagicWeatherClockAPI

A simple Python wrapper for controlling the **GeekMagic SmallTV** over your local network. Supports uploading images/GIFs, switching themes, adjusting brightness, and managing files on the device.

[PyPi Link](https://pypi.org/project/GeekMagicWeatherClockAPI/0.1.0/)

---

## Installation

```bash
pip install GeekMagicWeatherClockAPI
```

## Requirements

- Python 3.7+
- [`requests`](https://pypi.org/project/requests/) (installed automatically)

---

## Setup

Find your SmallTV's local IP address (check your router's device list or the SmallTV's settings menu), then:

```python
from GeekMagicWeatherClockAPI import SmallTV

tv = SmallTV("192.168.1.85")
```

---

## Usage

### Upload an image

```python
tv.upload("my_animation.gif")
tv.upload("my_animation.gif", retries=5)  # Custom retry count
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

## Full Example

```python
from GeekMagicWeatherClockAPI import SmallTV

tv = SmallTV("192.168.1.85")

tv.upload_and_set("spaceman.gif")
tv.set_brightness(30)
tv.set_theme("Weather Clock Today")
tv.replace("spaceman.gif", "new_image.gif")
tv.delete("new_image.gif")
```

---

## Notes

- The SmallTV firmware occasionally returns malformed `Content-Length` headers on upload responses. The `upload` method treats this as a failure and retries automatically.
- All methods can raise `requests.exceptions.ConnectionError` if the device is unreachable.
- File management methods operate on the `/image/` directory on the device.
