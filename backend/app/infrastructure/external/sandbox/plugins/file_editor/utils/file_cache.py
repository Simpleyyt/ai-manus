import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from openhands.sdk.logger import get_logger


logger = get_logger(__name__)


class FileCache:
    directory: Path
    size_limit: int | None
    current_size: int

    def __init__(self, directory: str, size_limit: int | None = None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.size_limit = size_limit
        self.current_size = 0
        self._update_current_size()
        logger.debug(
            f"FileCache initialized with directory: {self.directory}, "
            f"size_limit: {self.size_limit}, current_size: {self.current_size}"
        )

    def _get_file_path(self, key: str) -> Path:
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return self.directory / f"{hashed_key}.json"

    def _update_current_size(self):
        self.current_size = sum(
            f.stat().st_size for f in self.directory.glob("*.json") if f.is_file()
        )
        logger.debug(f"Current size updated: {self.current_size}")

    def set(self, key: str, value: Any) -> None:
        file_path = self._get_file_path(key)
        content = json.dumps({"key": key, "value": value})
        content_size = len(content.encode("utf-8"))
        logger.debug(f"Setting key: {key}, content_size: {content_size}")

        if self.size_limit is not None:
            if file_path.exists():
                old_size = file_path.stat().st_size
                size_diff = content_size - old_size
                logger.debug(
                    f"Existing file: old_size: {old_size}, size_diff: {size_diff}"
                )
                if size_diff > 0:
                    while (
                        self.current_size + size_diff > self.size_limit
                        and len(self) > 1
                    ):
                        logger.debug(
                            f"Evicting oldest (existing file case): "
                            f"current_size: {self.current_size}, "
                            f"size_limit: {self.size_limit}"
                        )
                        self._evict_oldest(file_path)
            else:
                while (
                    self.current_size + content_size > self.size_limit and len(self) > 1
                ):
                    logger.debug(
                        f"Evicting oldest (new file case): "
                        f"current_size: {self.current_size}, "
                        f"size_limit: {self.size_limit}"
                    )
                    self._evict_oldest(file_path)

        if file_path.exists():
            self.current_size -= file_path.stat().st_size
            logger.debug(
                f"Existing file removed from current_size: {self.current_size}"
            )

        with open(file_path, "w") as f:
            f.write(content)

        self.current_size += content_size
        logger.debug(f"File written, new current_size: {self.current_size}")
        os.utime(
            file_path, (time.time(), time.time())
        )  # Update access and modification time

    def _evict_oldest(self, exclude_path: Path | None = None):
        oldest_file = min(
            (
                f
                for f in self.directory.glob("*.json")
                if f.is_file() and f != exclude_path
            ),
            key=os.path.getmtime,
        )
        evicted_size = oldest_file.stat().st_size
        self.current_size -= evicted_size
        os.remove(oldest_file)
        logger.debug(
            f"Evicted file: {oldest_file}, size: {evicted_size}, "
            f"new current_size: {self.current_size}"
        )

    def get(self, key: str, default: Any = None) -> Any:
        file_path = self._get_file_path(key)
        if not file_path.exists():
            logger.debug(f"Get: Key not found: {key}")
            return default
        with open(file_path) as f:
            data = json.load(f)
            os.utime(file_path, (time.time(), time.time()))  # Update access time
            logger.debug(f"Get: Key found: {key}")
            return data["value"]

    def delete(self, key: str) -> None:
        file_path = self._get_file_path(key)
        if file_path.exists():
            deleted_size = file_path.stat().st_size
            self.current_size -= deleted_size
            os.remove(file_path)
            logger.debug(
                f"Deleted key: {key}, size: {deleted_size}, "
                f"new current_size: {self.current_size}"
            )

    def clear(self) -> None:
        for item in self.directory.glob("*.json"):
            if item.is_file():
                os.remove(item)
        self.current_size = 0
        logger.debug("Cache cleared")

    def __contains__(self, key: str) -> bool:
        exists = self._get_file_path(key).exists()
        logger.debug(f"Contains check: {key}, result: {exists}")
        return exists

    def __len__(self) -> int:
        length = sum(1 for _ in self.directory.glob("*.json") if _.is_file())
        logger.debug(f"Cache length: {length}")
        return length

    def __iter__(self):
        for file in self.directory.glob("*.json"):
            if file.is_file():
                with open(file) as f:
                    data = json.load(f)
                    logger.debug(f"Yielding key: {data['key']}")
                    yield data["key"]

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
