import requests
from pathlib import Path
from urllib.parse import quote


class SmallTV:
    """
    HTTP client for controlling a GeekMagic SmallTV device.

    All public methods return a standardized response dictionary::

        {
            "success":     bool,
            "status_code": int | None,
            "response":    str | None,
            "error":       str | None,
        }
    """

    THEMES: dict[int, str] = {
        1: "Weather Clock Today",
        2: "Weather Forecast",
        3: "Photo Album",
        4: "Time Style 1",
        5: "Time Style 2",
        6: "Time Style 3",
        7: "Simple Weather Clock",
    }

    _THEME_LOOKUP: dict[str, int] = {}  # populated lazily in __init__

    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.base_url = f"http://{ip}"

        self._THEME_LOOKUP = {v.lower(): k for k, v in self.THEMES.items()}

        self.session = requests.Session()
        self.session.headers.update({"X-Requested-With": "XMLHttpRequest"})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        success: bool,
        status_code: int | None = None,
        response: str | None = None,
        error: str | None = None,
    ) -> dict:
        return {
            "success": success,
            "status_code": status_code,
            "response": response,
            "error": error,
        }

    def _get(self, endpoint: str, **kwargs) -> dict:
        """
        Perform a GET request against *endpoint* (relative path + query string).

        Extra *kwargs* are forwarded to ``session.get()``.
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", 10)

        try:
            r = self.session.get(url, **kwargs)
            return self._build_result(
                success=r.ok,
                status_code=r.status_code,
                response=r.text,
            )
        except requests.RequestException as exc:
            return self._build_result(success=False, error=str(exc))
        except Exception as exc:
            return self._build_result(success=False, error=f"Unexpected error: {exc}")

    def _post(self, endpoint: str, **kwargs) -> dict:
        """
        Perform a POST request against *endpoint* (relative path + query string).

        Extra *kwargs* are forwarded to ``session.post()``.
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", 30)

        try:
            r = self.session.post(url, **kwargs)
            return self._build_result(
                success=r.ok,
                status_code=r.status_code,
                response=r.text,
            )
        except requests.exceptions.InvalidHeader as exc:
            # SmallTV firmware occasionally returns malformed response headers.
            return self._build_result(
                success=False,
                error=f"Malformed response headers from device: {exc}",
            )
        except requests.RequestException as exc:
            return self._build_result(success=False, error=str(exc))
        except Exception as exc:
            return self._build_result(success=False, error=f"Unexpected error: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload(self, file_path, retries: int = 3) -> dict:
        """
        Upload a GIF/image to the SmallTV.

        Retries up to *retries* times to work around malformed-header
        responses emitted by some SmallTV firmware versions.

        Returns a standardized result dict.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return self._build_result(
                success=False,
                error=f"File not found: {file_path}",
            )

        filename = file_path.name

        try:
            gif_data = file_path.read_bytes()
        except OSError as exc:
            return self._build_result(success=False, error=str(exc))

        last_result: dict = {}

        for attempt in range(1, retries + 1):
            # Clean up any partial upload from a previous failed attempt.
            if attempt > 1:
                self.delete(filename)

            files = {
                "update": (filename, gif_data, "image/gif"),
                "image": (filename, gif_data, "image/gif"),
            }

            result = self._post("/doUpload?dir=/image/", files=files)
            last_result = result

            if result["success"]:
                return result

            # Only retry on malformed-header errors (firmware quirk).
            if result.get("error") and "malformed" not in result["error"].lower():
                return result

        # All attempts exhausted — clean up and surface the last error.
        self.delete(filename)
        last_result["error"] = (
            f"Upload of '{filename}' failed after {retries} attempt(s). "
            f"Last error: {last_result.get('error')}"
        )
        return last_result

    def set_image(self, filename: str) -> dict:
        """
        Set the currently displayed image on the device.
        """
        encoded = quote(filename)
        return self._get(f"/set?img=/image/{encoded}")

    def set_theme(self, theme) -> dict:
        """
        Set the active SmallTV theme.

        *theme* may be an integer (1–7) or one of the theme name strings:

        * ``"Weather Clock Today"``
        * ``"Weather Forecast"``
        * ``"Photo Album"``
        * ``"Time Style 1"``
        * ``"Time Style 2"``
        * ``"Time Style 3"``
        * ``"Simple Weather Clock"``
        """
        if isinstance(theme, str):
            theme_id = self._THEME_LOOKUP.get(theme.lower())
            if theme_id is None:
                return self._build_result(
                    success=False,
                    error=f"Unknown theme '{theme}'. Valid themes: {list(self.THEMES.values())}",
                )
        else:
            try:
                theme_id = int(theme)
            except (TypeError, ValueError) as exc:
                return self._build_result(success=False, error=str(exc))

        if theme_id not in self.THEMES:
            return self._build_result(
                success=False,
                error=f"Theme ID must be between 1 and 7, got {theme_id}.",
            )

        return self._get(f"/set?theme={theme_id}")

    def set_brightness(self, value) -> dict:
        """
        Set the display brightness (0–100).
        """
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            return self._build_result(success=False, error=str(exc))

        if not 0 <= value <= 100:
            return self._build_result(
                success=False,
                error=f"Brightness must be between 0 and 100, got {value}.",
            )

        return self._get(f"/set?brt={value}")

    def delete(self, filename: str) -> dict:
        """
        Delete an image from the device.
        """
        encoded = quote(filename)
        return self._get(f"/delete?file=/image/{encoded}")

    def upload_and_set(self, file_path) -> dict:
        """
        Upload a file and immediately display it.

        Returns the result of ``set_image`` on success, or the failed
        ``upload`` result if the upload did not succeed.
        """
        file_path = Path(file_path)

        upload_result = self.upload(file_path)
        if not upload_result["success"]:
            return upload_result

        return self.set_image(file_path.name)

    def replace(self, old_filename: str, new_file) -> dict:
        """
        Delete *old_filename*, upload *new_file*, and display it.

        The delete step is best-effort; failure does not abort the operation.
        Returns the result of ``upload_and_set``.
        """
        self.delete(old_filename)
        return self.upload_and_set(new_file)