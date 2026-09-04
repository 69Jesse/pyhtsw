import tempfile
from pathlib import Path
from typing import Any

from pyhtsw import (
    Container,
    chat,
    function,
)

tmp = Path(tempfile.mkdtemp())


def build(container: Container) -> None:
    with container:

        @function('Foo')
        def foo() -> None:
            chat('hi')


calls: list[tuple[Any, ...]] = []


# A hook may take 0, 1 or 2 arguments.
no_args = Container(projects_folder=tmp, post_export=lambda: calls.append(()))
build(no_args)
no_args.export('Hook None')

one_arg = Container(projects_folder=tmp, post_export=lambda path: calls.append((path,)))
build(one_arg)
one_arg.export('Hook One')

two_args = Container(
    projects_folder=tmp,
    post_export=lambda path, container: calls.append((path, container)),
)
build(two_args)
two_args.export('Hook Two')

assert calls[0] == ()
assert calls[1] == (tmp / 'hook-one',)
assert calls[2] == (tmp / 'hook-two', two_args)


# The hook runs after the files are on disk, so it can rewrite the tree.
def flatten(root: Path) -> None:
    for htsl in root.rglob('*.htsl'):
        htsl.rename(root / htsl.name)
    (root / 'functions').rmdir()
    (root / 'import.json').unlink()


rewriting = Container(projects_folder=tmp, post_export=flatten)
build(rewriting)
rewriting.export('Hook Rewrite')

root = tmp / 'hook-rewrite'
assert (root / 'foo.htsl').exists()
assert not (root / 'functions').exists()
assert not (root / 'import.json').exists()


# A bound method's `self` does not count towards the argument count.
class Recorder:
    def __init__(self) -> None:
        self.seen: Path | None = None

    def __call__(self, path: Path) -> None:
        self.seen = path

    def record(self, path: Path) -> None:
        self.seen = path


method = Recorder()
bound = Container(projects_folder=tmp, post_export=method.record)
build(bound)
bound.export('Hook Method')
assert method.seen == tmp / 'hook-method'

instance = Recorder()
callable_object = Container(projects_folder=tmp, post_export=instance)
build(callable_object)
callable_object.export('Hook Object')
assert instance.seen == tmp / 'hook-object'


# An unset hook falls through to the global container.
import pyhtsw  # noqa: E402

global_calls: list[Path] = []
pyhtsw.configure(post_export=global_calls.append)
inheriting = Container(projects_folder=tmp)
build(inheriting)
inheriting.export('Hook Inherited')
assert global_calls == [tmp / 'hook-inherited']
pyhtsw.configure(post_export=None)


# Too many required arguments is an error, not a silent miscall.
greedy = Container(
    projects_folder=tmp,
    post_export=lambda a, b, c: None,  # pyright: ignore[reportUnknownLambdaType]
)
build(greedy)
try:
    greedy.export('Hook Greedy')
except ValueError as error:
    assert 'post_export hook' in str(error), error
else:
    raise AssertionError('expected a ValueError for a 3-argument hook')

# A non-callable is rejected where it is set, not at export.
try:
    Container(post_export=42)  # pyright: ignore[reportArgumentType]
except TypeError as error:
    assert 'callable' in str(error), error
else:
    raise AssertionError('expected a TypeError for a non-callable hook')
