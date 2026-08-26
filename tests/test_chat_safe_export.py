import tempfile
from pathlib import Path

from helpers import expect_exception

from pyhtsw.compiler.importable import Project, _verify_chat_safe

CLEAN = 'var "s" = "&aok" true\nvar "t" = "%player.name%" true'

# Clean content passes untouched.
_verify_chat_safe('functions/clean.htsl', CLEAN)

# Every character the chat box filters is rejected, wherever it sits. A newline
# is the exception: it separates HTSL lines, and one landing inside a value
# leaves htsw an unterminated string to report rather than a live kick.
for offender in [chr(code) for code in range(0x20) if code != 0x0A] + ['\x7f', '§']:
    with expect_exception(ValueError):
        _verify_chat_safe('functions/bad.htsl', f'var "s" = "a{offender}b" true')

# The message locates the character: path, line, column, and the code point.
try:
    _verify_chat_safe('functions/bad.htsl', f'{CLEAN}\nvar "s" = "a\x00b" true')
except ValueError as error:
    message = str(error)
    assert 'functions/bad.htsl:3:13' in message, message
    assert 'U+0000' in message, message
else:
    raise AssertionError('expected ValueError for a NUL in emitted HTSL')


# Only .htsl is checked — .snbt item display names legitimately carry §.
writer = Project(Path(tempfile.mkdtemp()))
writer.write(
    'items/wand.snbt',
    '{id: "minecraft:stick", tag: {display: {Name: "§6Wand"}}}',
)

with expect_exception(ValueError):
    writer.write('functions/bad.htsl', 'var "s" = "a\x00b" true')
