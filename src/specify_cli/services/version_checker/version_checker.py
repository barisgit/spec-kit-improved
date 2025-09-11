"""PyPI version checker with caching and ETag support."""

import contextlib
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from packaging.version import parse
from platformdirs import user_cache_dir

from specify_cli.utils.file_operations import ensure_directory


class PyPIVersionChecker:
    """Check for updates from PyPI with intelligent caching."""

    def __init__(self, package_name: str = "specifyx"):
        # TODO: Move hardcoded values to constants.py
        self.package_name = package_name
        self.cache_dir = Path(user_cache_dir("specifyx", "SpecifyX"))
        self.cache_file = self.cache_dir / "version_cache.json"
        self.cache_duration = timedelta(minutes=15)  # 15-minute cache
        self.api_url = f"https://pypi.org/pypi/{package_name}/json"
        self.user_agent = (
            f"specifyx/{self._get_current_version()} (pypi-update-checker)"
        )

    def _get_current_version(self) -> str:
        """Get current version from package metadata."""
        try:
            from importlib.metadata import version

            return version(self.package_name)
        except Exception:
            return "0.0.0"

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached version data if still valid."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            last_check = datetime.fromisoformat(cache_data["last_check"])
            if datetime.now(timezone.utc) - last_check < self.cache_duration:
                return cache_data
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache, will refresh
            pass

        return None

    def _read_cache_stale(self) -> Optional[Dict[str, Any]]:
        """Read cache without validating TTL for stale fallback/ETag reuse."""
        try:
            with open(self.cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save version data to cache."""
        try:
            ensure_directory(self.cache_dir)
            data["last_check"] = datetime.now(timezone.utc).isoformat()

            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Cache save failure should not break functionality
            pass

    def _fetch_latest_version(
        self, cached_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Fetch latest version from PyPI with ETag support."""
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        # Add ETag header for conditional request if available
        if cached_data and "etag" in cached_data:
            headers["If-None-Match"] = cached_data["etag"]

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.api_url, headers=headers)

                # Explicitly handle known good statuses
                if response.status_code == 304 and cached_data:
                    return cached_data.get("latest_version")

                if response.status_code == 200:
                    data = response.json()
                    latest_version = data["info"]["version"]

                    # Save new cache data with ETag
                    cache_data = {
                        "latest_version": latest_version,
                        "current_version": self._get_current_version(),
                        "etag": response.headers.get("etag"),
                    }
                    self._save_cache(cache_data)

                    return latest_version

                # Any other status: warn and fallback to cached
                logging.warning(
                    "PyPI version check returned status %s for %s",
                    response.status_code,
                    self.api_url,
                )
        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
            KeyError,
            json.JSONDecodeError,
        ):
            # Network or parsing errors - warn and return cached version if available
            logging.warning(
                "PyPI version check failed; using cached version if available",
                exc_info=False,
            )
            if cached_data:
                return cached_data.get("latest_version")

        # No usable result
        return cached_data.get("latest_version") if cached_data else None

    def check_for_updates(
        self, use_cache: bool = True
    ) -> tuple[bool, str, Optional[str]]:
        """
        Check if updates are available.

        Returns:
                tuple[bool, str, Optional[str]]: (has_update, current_version, latest_version)
        """
        current_version = self._get_current_version()

        # Load fresh and stale caches (stale used for ETag/offline fallback)
        fresh_cache = self._load_cache() if use_cache else None
        stale_cache = self._read_cache_stale() if use_cache else None

        # Only bypass network when cache is fresh and matches current version
        if fresh_cache and fresh_cache.get("current_version") == current_version:
            latest_version = fresh_cache.get("latest_version")
        else:
            latest_version = self._fetch_latest_version(stale_cache)

        # If we couldn't get latest version, return no update available
        if latest_version is None:
            return False, current_version, None

        # Compare versions using packaging.version
        try:
            has_update = parse(latest_version) > parse(current_version)
            return has_update, current_version, latest_version
        except Exception:
            # Version parsing error - assume no update
            return False, current_version, latest_version

    def get_latest_version(self, use_cache: bool = True) -> Optional[str]:
        """Get the latest version from PyPI."""
        stale_cache = self._read_cache_stale() if use_cache else None
        fresh_cache = self._load_cache() if use_cache else None
        if fresh_cache:
            # If fresh cache exists, return its value directly for fast path
            return fresh_cache.get("latest_version")
        return self._fetch_latest_version(stale_cache)

    def clear_cache(self) -> None:
        """Clear the version cache."""
        if self.cache_file.exists():
            with contextlib.suppress(Exception):
                self.cache_file.unlink()

    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """Get cache information for debugging."""
        cache_data = self._load_cache()
        if cache_data:
            cache_data["cache_file"] = str(self.cache_file)
            cache_data["cache_age_hours"] = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(cache_data["last_check"])
            ).total_seconds() / 3600
        return cache_data
