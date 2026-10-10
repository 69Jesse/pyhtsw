import json
import os
import sys
from pathlib import Path
from typing import Any

__all__ = (
    'LOCK_FILE_NAME',
    'Lock',
    'as_lock_file',
    'lock_at',
)

LOCK_FILE_NAME = 'pyhtsw.lock'
LOCK_VERSION = 1


class Lock:
    """Compile-time state that has to survive between builds, in one file.

    Each subsystem owns a section, addressed by a key path. The file is read
    on first use and written only by a successful export, so it always
    describes what the house last imported."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
        data: dict[str, Any] = {}
        if self.path.exists():
            raw: object = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                raise ValueError(f'{self.path} is not a pyhtsw lock file')
            data = dict(raw)
            version = data.pop('version', LOCK_VERSION)
            if version != LOCK_VERSION:
                raise ValueError(
                    f'{self.path} is lock version {version}; this pyhtsw reads '
                    f'version {LOCK_VERSION}',
                )
        self._data = data
        return data

    def section(self, *keys: str) -> dict[str, Any]:
        node = self._load()
        for key in keys:
            child = node.setdefault(key, {})
            if not isinstance(child, dict):
                raise ValueError(
                    f'{self.path}: section {"/".join(keys)!r} is not an object',
                )
            node = child
        return node

    def render(self) -> str | None:
        data = _pruned(self._load())
        if not data:
            return None
        return json.dumps({'version': LOCK_VERSION, **data}, indent=2) + '\n'

    def save(self) -> None:
        content = self.render()
        if content is None:
            return
        if self.path.exists() and self.path.read_text(encoding='utf-8') == content:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        part = self.path.with_name(self.path.name + '.part')
        part.write_text(content, encoding='utf-8')
        os.replace(part, self.path)


def _pruned(node: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in node.items():
        if isinstance(value, dict):
            value = _pruned(value)
            if not value:
                continue
        out[key] = value
    return out


_LOCKS: dict[Path, Lock] = {}


def lock_at(path: Path) -> Lock:
    path = path.resolve()
    lock = _LOCKS.get(path)
    if lock is None:
        lock = _LOCKS[path] = Lock(path)
    return lock


def _entry_dir() -> Path:
    script = Path(sys.argv[0]) if sys.argv and sys.argv[0] else None
    if script is not None and script.is_file():
        return script.resolve().parent
    return Path.cwd()


def as_lock_file(value: 'Path | str | None') -> Path | None:
    if value is None:
        return None
    path = Path(value)
    return path if path.is_absolute() else _entry_dir() / path
