import requests
from pathlib import Path
from urllib.parse import quote


class SmallTV:
    def __init__(self, ip: str):
        self.ip = ip
        self.base_url = f"http://{ip}"
        self.THEMES = {
            1: "Weather Clock Today",
            2: "Weather Forecast",
            3: "Photo Album",
            4: "Time Style 1",
            5: "Time Style 2",
            6: "Time Style 3",
            7: "Simple Weather Clock",
        }

    def upload(self, file_path, retries=3):
        """
        Upload a GIF/image to the SmallTV.
        Retries on malformed header responses from SmallTV firmware.
        """

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        filename = file_path.name

        with open(file_path, "rb") as f:
            gif_data = f.read()

        headers = {
            "X-Requested-With": "XMLHttpRequest"
        }

        for attempt in range(1, retries + 1):
            # Delete any partial/failed upload before retrying
            if attempt > 1:
                print(f"Cleaning up failed upload, retrying... (attempt {attempt}/{retries})")
                try:
                    self.delete(filename)
                except Exception:
                    pass

            files = {
                "update": (filename, gif_data, "image/gif"),
                "image": (filename, gif_data, "image/gif"),
            }

            try:
                r = requests.post(
                    f"{self.base_url}/doUpload?dir=/image/",
                    files=files,
                    headers=headers,
                    timeout=30
                )
                print("Upload Status:", r.status_code)
                return True

            except requests.exceptions.InvalidHeader:
                print(f"Upload failed (malformed headers from SmallTV firmware) — attempt {attempt}/{retries}")
                if attempt == retries:
                    try:
                        self.delete(filename)
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Upload of '{filename}' failed after {retries} attempts."
                    )

        return False

    def set_image(self, filename):
        """
        Set the currently displayed image.
        """

        encoded_filename = quote(filename)

        r = requests.get(
            f"{self.base_url}/set?img=/image/{encoded_filename}",
            timeout=10
        )

        print("Set Status:", r.status_code)

        return r
    
    def set_theme(self, theme):
        """
        Set the SmallTV theme.

        Accepts:
            1-7
            or
            "Weather Clock Today"
            "Weather Forecast"
            "Photo Album"
            "Time Style 1"
            "Time Style 2"
            "Time Style 3"
            "Simple Weather Clock"
        """

        if isinstance(theme, str):
            theme_lookup = {
                v.lower(): k
                for k, v in self.THEMES.items()
            }

            theme_id = theme_lookup.get(theme.lower())

            if theme_id is None:
                raise ValueError(
                    f"Unknown theme '{theme}'"
                )
        else:
            theme_id = int(theme)

        if theme_id not in self.THEMES:
            raise ValueError(
                f"Theme must be between 1 and 7"
            )

        r = requests.get(
            f"{self.base_url}/set?theme={theme_id}",
            timeout=10
        )

        print(
            f"Theme set to {theme_id}: "
            f"{self.THEMES[theme_id]}"
        )
        print("Status:", r.status_code)

        return r
    
    def set_brightness(self, value):
        """
        Set SmallTV brightness (0–100).
        """

        value = int(value)

        if value < 0 or value > 100:
            raise ValueError("Brightness must be between 0 and 100")

        r = requests.get(
            f"{self.base_url}/set?brt={value}",
            timeout=10
        )

        print(f"Brightness set to {value}")
        print("Status:", r.status_code)

        return r

    def delete(self, filename):
        """
        Delete an image from the SmallTV.
        """

        encoded_filename = quote(filename)

        r = requests.get(
            f"{self.base_url}/delete?file=/image/{encoded_filename}",
            timeout=10
        )

        print("Delete Status:", r.status_code)

        return r

    def upload_and_set(self, file_path):
        """
        Upload a file and immediately display it.
        """

        file_path = Path(file_path)

        self.upload(file_path)

        return self.set_image(file_path.name)

    def replace(self, old_filename, new_file):
        """
        Delete an old image, upload a new one, and display it.
        """

        try:
            self.delete(old_filename)
        except Exception:
            pass

        return self.upload_and_set(new_file)