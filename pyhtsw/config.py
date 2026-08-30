import os
from pathlib import Path

from pyhtsw.utils.log import log

__all__ = (
    'set_projects_folder',
    'get_projects_folder',
    'resolve_projects_folder',
    'remember_projects_folder',
)


HERE: Path = Path(__file__).parent


def _config_folder() -> Path:
    if os.name == 'nt':
        base = Path(os.getenv('APPDATA') or Path.home())
    else:
        base = Path(os.getenv('XDG_CONFIG_HOME') or (Path.home() / '.config'))
    return base / 'pyhtsw'


CACHED_PROJECTS_FOLDER_PATH: Path = _config_folder() / 'projects-folder.txt'
LEGACY_CACHED_PROJECTS_FOLDER_PATH: Path = HERE / 'cached_projects_folder.txt'


def _default_projects_folder() -> Path | None:
    if os.name == 'nt':
        return Path(os.getenv('APPDATA') or '') / '.minecraft' / 'htsw' / 'projects'
    if os.name == 'posix':
        return (
            Path.home()
            / 'Library'
            / 'Application Support'
            / 'minecraft'
            / 'htsw'
            / 'projects'
        )
    return None


_PROJECTS_FOLDER_OVERRIDE: Path | None = None


def set_projects_folder(folder: Path | str, *, save: bool = False) -> None:
    """Point exports at `folder` for this run. Pass `save=True` to remember it
    for future runs; the default deliberately leaves the cached folder alone, so
    a test or benchmark cannot clobber the real one."""
    folder = Path(folder).resolve()

    global _PROJECTS_FOLDER_OVERRIDE
    _PROJECTS_FOLDER_OVERRIDE = folder

    if save:
        remember_projects_folder(folder)


def remember_projects_folder(folder: Path | str) -> None:
    """Write `folder` to the cache every future run reads."""
    folder = Path(folder).resolve()
    new_content = folder.as_posix()
    content = (
        CACHED_PROJECTS_FOLDER_PATH.read_text(encoding='utf-8')
        if CACHED_PROJECTS_FOLDER_PATH.exists()
        else None
    )
    if content == new_content:
        return
    CACHED_PROJECTS_FOLDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHED_PROJECTS_FOLDER_PATH.write_text(new_content, encoding='utf-8')
    log(
        f'\nSaved your HTSW projects folder \x1b[38;2;0;255;0m{folder.as_posix()}\x1b[0m for future use at\n\x1b[38;2;0;255;0m{CACHED_PROJECTS_FOLDER_PATH}\x1b[0m',
    )


def _cached_projects_folder() -> Path | None:
    for path in (CACHED_PROJECTS_FOLDER_PATH, LEGACY_CACHED_PROJECTS_FOLDER_PATH):
        if not path.exists():
            continue
        raw_path = path.read_text(encoding='utf-8').strip()
        if raw_path:
            return Path(raw_path)
    return None


def resolve_projects_folder() -> Path | None:
    """The configured projects folder, or None if there is nothing to go on.
    Pure: it neither prompts nor writes, so it is safe to call from anywhere."""
    if _PROJECTS_FOLDER_OVERRIDE is not None:
        return _PROJECTS_FOLDER_OVERRIDE
    cached = _cached_projects_folder()
    if cached is not None:
        return cached
    return _default_projects_folder()


def get_projects_folder() -> Path:
    """The projects folder to export into, asking for one if this machine has
    never had it resolved. Prompts on stdin, so only the export path calls it."""
    if _PROJECTS_FOLDER_OVERRIDE is not None:
        return _PROJECTS_FOLDER_OVERRIDE
    cached = _cached_projects_folder()
    if cached is not None:
        cached = cached.resolve()
        remember_projects_folder(cached)
        return cached
    default = _default_projects_folder()
    if default is not None:
        default = default.resolve()
        remember_projects_folder(default)
        return default

    log('\x1b[38;2;255;0;0mCould not determine your HTSW projects folder.\x1b[0m')
    while True:
        log(
            'Please enter the path to your \x1b[38;2;0;255;0mHTSW projects folder\x1b[0m (relative or absolute): ',
            end='',
        )
        raw_path = input().strip()
        if not raw_path:
            log('\x1b[38;2;255;0;0mPlease provide a valid path.\x1b[0m')
            continue
        set_projects_folder(raw_path, save=True)
        return Path(raw_path).resolve()
