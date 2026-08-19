import re
import string
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Self

import numpy as np


class NBT[T](ABC):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    @abstractmethod
    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        """
        Convert the NBT object to a string in SNBT format.
        """
        raise NotImplementedError

    @abstractmethod
    def into_object(self) -> Any:
        """
        Convert the NBT object to a Python object.
        """
        raise NotImplementedError

    WHITESPACE: str = ' \t\n\r'

    @staticmethod
    def skip_whitespace(s: str, offset: int = 0) -> int:
        """
        Return the first offset at or after `offset` that isn't whitespace.
        """
        while offset < len(s) and s[offset] in NBT.WHITESPACE:
            offset += 1
        return offset

    @classmethod
    def from_snbt(cls, s: str) -> 'NBT':
        """
        Load the NBT object from a string in SNBT format.
        Raises an exception if the string is not valid SNBT.
        """
        start = cls.skip_whitespace(s)
        nbt, length = cls._parse_snbt(s[start:])
        offset = cls.skip_whitespace(s, start + length)
        if offset == len(s):
            return nbt
        raise ValueError(
            f'Invalid SNBT format: {repr(s)} ({len(s) - offset} characters left)',
        )

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        for subclass in PARSE_ORDER:
            try:
                return subclass._parse_snbt(s)  # type: ignore
            except ValueError:
                continue
        raise ValueError(f'Invalid SNBT format: {repr(s)}')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBT':
        """
        Load the NBT object from a Python object.
        Raises an exception if the object is not valid.
        """
        if isinstance(obj, NBT):
            return obj
        for subclass in cls.__subclasses__():
            if subclass is NBT:
                continue
            try:
                return subclass.from_object(obj)
            except Exception:
                continue
        raise ValueError(f'Invalid object for NBT: {repr(obj)}')

    def __str__(self) -> str:
        return self.into_snbt()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{repr(self.value)}>'


class NBTByte(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -128 <= value <= 127:
            raise ValueError('Value must be between -128 and 127')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return f'{self.into_object()}b'

    def into_object(self) -> int:
        return self.value

    BYTE_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,3}[bB]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.BYTE_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTByte':
        if isinstance(obj, NBTByte):
            return obj
        return cls(obj)


class NBTBoolean(NBTByte):
    def __init__(self, value: int | bool = False) -> None:
        if isinstance(value, int):
            if value not in (0, 1):
                raise ValueError('Value must be 0 or 1 for NBTBoolean')
            value = bool(value)
        if not isinstance(value, bool):
            raise TypeError('Value must be a boolean')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return 'true' if self.value else 'false'

    def into_object(self) -> bool:
        return self.value  # type: ignore

    BOOLEAN_REGEX: re.Pattern[str] = re.compile(r'^(true|false|[10][bB])', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.BOOLEAN_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = match.group(0)
        if value in ('true', '1b', '1B'):
            return cls(True), match.end(0)
        elif value in ('false', '0b', '0B'):
            return cls(False), match.end(0)
        raise ValueError(f'Invalid SNBT format for {cls.__name__}')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTBoolean':
        if isinstance(obj, NBTBoolean):
            return obj
        return cls(obj)


class NBTShort(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -32768 <= value <= 32767:
            raise ValueError('Value must be between -32768 and 32767')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return f'{self.into_object()}s'

    def into_object(self) -> int:
        return self.value

    SHORT_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,5}[sS]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.SHORT_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTShort':
        if isinstance(obj, NBTShort):
            return obj
        return cls(obj)


class NBTInt(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -2147483648 <= value <= 2147483647:
            raise ValueError('Value must be between -2147483648 and 2147483647')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return str(self.into_object())

    def into_object(self) -> int:
        return self.value

    INT_REGEX: re.Pattern[str] = re.compile(r'^-?\d+(?![.\d])', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.INT_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = int(match.group(0))
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTInt':
        if isinstance(obj, NBTInt):
            return obj
        return cls(obj)


class NBTLong(NBT[int]):
    def __init__(self, value: int = 0) -> None:
        if not isinstance(value, int):
            raise TypeError('Value must be an integer')
        if not -9223372036854775808 <= value <= 9223372036854775807:
            raise ValueError(
                'Value must be between -9223372036854775808 and 9223372036854775807',
            )
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return f'{self.into_object()}l'

    def into_object(self) -> int:
        return self.value

    LONG_REGEX: re.Pattern[str] = re.compile(r'^-?\d{1,19}[lL]', re.ASCII)

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.LONG_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = int(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTLong':
        if isinstance(obj, NBTLong):
            return obj
        return cls(obj)


class NBTFloat(NBT[float]):
    def __init__(self, value: float = 0.0) -> None:
        if not isinstance(value, float):
            raise TypeError('Value must be a float')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        formatted = np.format_float_positional(self.into_object(), trim='-')
        if '.' not in formatted:
            formatted += '.0'
        return f'{formatted}f'

    def into_object(self) -> float:
        return self.value

    # E notation is accepted but never written: `into_snbt` stays positional so
    # older readers keep working. Vanilla's own writer does emit it for extreme
    # magnitudes, though, so files from elsewhere can carry it.
    FLOAT_REGEX: re.Pattern[str] = re.compile(
        r'^-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fF]',
        re.ASCII,
    )

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.FLOAT_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        value = float(match.group(0)[:-1])
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTFloat':
        if isinstance(obj, NBTFloat):
            return obj
        return cls(obj)


class NBTDouble(NBT[float]):
    def __init__(self, value: float = 0.0) -> None:
        if not isinstance(value, float):
            raise TypeError('Value must be a float')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        formatted = np.format_float_positional(self.into_object(), trim='-')
        if '.' not in formatted:
            formatted += '.0'
        return formatted

    def into_object(self) -> float:
        return self.value

    # An unsuffixed double needs a decimal point or an exponent, otherwise it
    # would swallow ints. E notation is accepted but never written — see
    # NBTFloat.FLOAT_REGEX.
    DOUBLE_REGEX: re.Pattern[str] = re.compile(
        r'^-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[dD]'
        r'|^-?(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)',
        re.ASCII,
    )

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        match = cls.DOUBLE_REGEX.match(s)
        if not match:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        raw = match.group(0)
        if raw.endswith(('d', 'D')):
            raw = raw[:-1]
        value = float(raw)
        return cls(value), match.end(0)

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTDouble':
        if isinstance(obj, NBTDouble):
            return obj
        return cls(obj)


class NBTString(NBT[str]):
    def __init__(self, value: str = '') -> None:
        if not isinstance(value, str):
            raise TypeError('Value must be a string')
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        return f'"{self.escaped(self.into_object())}"'

    def into_object(self) -> str:
        return self.value

    QUOTES: tuple[str, str] = ('"', "'")

    # The escape set Minecraft 1.21.5 introduced. Before that release SNBT knew
    # only `\\` and `\<quote>`, so a string carrying control characters had no
    # representation at all: writers emitted them raw and the resulting file was
    # unparseable. Decoding is strict — an unknown escape is an error rather than
    # being kept literally, which is what the old parser did.
    SHORT_ESCAPES: dict[str, str] = {
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        's': ' ',
        't': '\t',
        '\\': '\\',
        "'": "'",
        '"': '"',
    }
    # Fixed widths, so the decoder always knows where the escape ends.
    HEX_ESCAPES: dict[str, int] = {'x': 2, 'u': 4, 'U': 8}
    # The reverse direction only needs the characters that must not appear raw.
    ESCAPE_FOR: dict[str, str] = {
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\\': '\\\\',
        '"': '\\"',
    }

    @staticmethod
    def escaped(value: str) -> str:
        """
        Escape `value` for a double-quoted SNBT literal.

        Only what has to be escaped is. Printable non-ASCII stays literal so
        files remain readable, and text without control characters comes out
        byte-identical to what the pre-1.21.5 dialect produced.
        """
        out: list[str] = []
        for character in value:
            short = NBTString.ESCAPE_FOR.get(character)
            if short is not None:
                out.append(short)
                continue
            code = ord(character)
            if code < 0x20 or code == 0x7F:
                out.append(f'\\x{code:02x}')
                continue
            if 0xD800 <= code <= 0xDFFF:
                # A lone surrogate has no UTF-8 encoding, so left literal it
                # would not survive being written to a file at all.
                out.append(f'\\u{code:04x}')
                continue
            out.append(character)
        return ''.join(out)

    @classmethod
    def _parse_escape(cls, s: str, offset: int) -> tuple[str, int]:
        if offset + 1 >= len(s):
            raise ValueError(
                f'Invalid SNBT format for {cls.__name__}: trailing backslash',
            )
        marker = s[offset + 1]

        width = cls.HEX_ESCAPES.get(marker)
        if width is not None:
            digits = s[offset + 2 : offset + 2 + width]
            if len(digits) < width or any(c not in string.hexdigits for c in digits):
                raise ValueError(
                    f'Invalid SNBT format for {cls.__name__}: '
                    f'\\{marker} needs {width} hex digits',
                )
            code = int(digits, 16)
            if code > 0x10FFFF:
                raise ValueError(
                    f'Invalid SNBT format for {cls.__name__}: '
                    f'\\{marker}{digits} is not a code point',
                )
            return chr(code), 2 + width

        if marker == 'N':
            if offset + 2 >= len(s) or s[offset + 2] != '{':
                raise ValueError(
                    f'Invalid SNBT format for {cls.__name__}: \\N needs a {{name}}',
                )
            end = s.find('}', offset + 3)
            if end == -1:
                raise ValueError(
                    f'Invalid SNBT format for {cls.__name__}: unterminated \\N{{',
                )
            try:
                return unicodedata.lookup(s[offset + 3 : end]), end + 1 - offset
            except KeyError as error:
                raise ValueError(
                    f'Invalid SNBT format for {cls.__name__}: '
                    f'unknown character name {s[offset + 3 : end]!r}',
                ) from error

        simple = cls.SHORT_ESCAPES.get(marker)
        if simple is not None:
            return simple, 2

        raise ValueError(
            f'Invalid SNBT format for {cls.__name__}: unknown escape \\{marker}',
        )

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        if not s or s[0] not in cls.QUOTES:
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        quote = s[0]
        characters: list[str] = []
        offset = 1
        while offset < len(s):
            character = s[offset]
            if character == '\\':
                decoded, consumed = cls._parse_escape(s, offset)
                characters.append(decoded)
                offset += consumed
                continue
            if character == quote:
                return cls(''.join(characters)), offset + 1
            characters.append(character)
            offset += 1
        raise ValueError(f'Invalid SNBT format for {cls.__name__}')

    @classmethod
    def from_object(cls, obj: Any) -> 'NBTString':
        if isinstance(obj, NBTString):
            return obj
        return cls(obj)


class NBTList[T: NBT](NBT[list[T]]):
    def __init__(self, value: list[T] | None = None) -> None:
        if value is None:
            value = []
        if not isinstance(value, list):
            raise TypeError('Value must be a list')
        if len(value) > 0:
            if not isinstance(value[0], NBT):
                raise ValueError('All items must be NBT instances')
            for i in range(1, len(value)):
                if not isinstance(value[i], value[0].__class__):
                    raise ValueError(
                        f'All items must be instances of {value[0].__class__.__name__}',
                    )
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        if indent is None:
            return f'[{",".join(item.into_snbt(None) for item in self.value)}]'
        if not self.value:
            return '[]'
        inner = ' ' * (indent * (level + 1))
        outer = ' ' * (indent * level)
        body = ',\n'.join(
            f'{inner}{item.into_snbt(indent, level + 1)}' for item in self.value
        )
        return f'[\n{body}\n{outer}]'

    def into_object(self) -> list[T]:
        return [item.into_object() for item in self.value]

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        if not s.startswith('['):
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        offset = cls.skip_whitespace(s, 1)
        items: list[T] = []
        while True:
            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == ']':
                return cls(items), offset + 1

            maybe_prefix = f'{len(items)}:'
            if s.startswith(maybe_prefix, offset):
                offset = cls.skip_whitespace(s, offset + len(maybe_prefix))

            item, length = NBT._parse_snbt(s[offset:])
            items.append(item)  # type: ignore
            offset = cls.skip_whitespace(s, offset + length)

            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == ']':
                return cls(items), offset + 1
            if s[offset] != ',':
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            offset = cls.skip_whitespace(s, offset + 1)

    @classmethod
    def from_object(cls, obj: list[T]) -> 'NBTList[T]':
        if isinstance(obj, NBTList):
            return obj
        if not isinstance(obj, list):
            raise TypeError('Value must be a list')
        return cls([NBT.from_object(item) for item in obj])  # type: ignore

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def __getitem__(self, index: int) -> T:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        return self.value[index]

    def __setitem__(self, index: int, value: T) -> None:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        if len(self.value) > 0:
            if not isinstance(value, self.value[0].__class__):
                raise ValueError(
                    f'Value must be an instance of {self.value[0].__class__.__name__}',
                )
        self.value[index] = value

    def append(self, value: T) -> Self:
        if len(self.value) > 0:
            if not isinstance(value, self.value[0].__class__):
                raise ValueError(
                    f'Value must be an instance of {self.value[0].__class__.__name__}',
                )
        self.value.append(value)
        return self


class NBTCompound[V: NBT](NBT[dict[str, V]]):
    def __init__(self, value: dict[str, V] | None = None) -> None:
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise TypeError('Value must be a dictionary')
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError('Keys must be strings')
            if not isinstance(item, NBT):
                raise ValueError('All items must be NBT instances')
        super().__init__(value)

    @staticmethod
    def _format_key(key: str) -> str:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            return f'"{NBTString.escaped(key)}"'
        return key

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        if indent is None:
            return (
                '{'
                + ','.join(
                    f'{self._format_key(key)}:{item.into_snbt(None)}'
                    for key, item in self.value.items()
                )
                + '}'
            )
        if not self.value:
            return '{}'
        inner = ' ' * (indent * (level + 1))
        outer = ' ' * (indent * level)
        body = ',\n'.join(
            f'{inner}{self._format_key(key)}: {item.into_snbt(indent, level + 1)}'
            for key, item in self.value.items()
        )
        return f'{{\n{body}\n{outer}}}'

    def into_object(self) -> dict[str, Any]:
        return {key: item.into_object() for key, item in self.value.items()}

    # Wider than `_format_key`: unquoted keys may legally contain digits, `-`, `.` and `+`.
    KEY_REGEX: re.Pattern[str] = re.compile(r'^[a-zA-Z0-9_+.\-]+$')

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        if not s.startswith('{'):
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        offset = cls.skip_whitespace(s, 1)
        compound: dict[str, V] = {}
        while True:
            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == '}':
                return cls(compound), offset + 1

            if s[offset] in NBTString.QUOTES:
                key_nbt, length = NBTString._parse_snbt(s[offset:])
                key = key_nbt.into_object()
                offset = cls.skip_whitespace(s, offset + length)
            else:
                key_start = offset
                while offset < len(s) and s[offset] not in (':', ',', '}'):
                    offset += 1
                key = s[key_start:offset].strip()
                if not cls.KEY_REGEX.match(key):
                    raise ValueError(
                        f'Invalid key format in {cls.__name__}: {repr(key)}',
                    )
            if offset >= len(s) or s[offset] != ':':
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')

            if key in compound:
                raise ValueError(f'Duplicate key found in {cls.__name__}: {repr(key)}')

            offset = cls.skip_whitespace(s, offset + 1)
            value, length = NBT._parse_snbt(s[offset:])
            compound[key] = value  # type: ignore
            offset = cls.skip_whitespace(s, offset + length)

            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == '}':
                return cls(compound), offset + 1
            if s[offset] != ',':
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            offset = cls.skip_whitespace(s, offset + 1)

    @classmethod
    def from_object(cls, obj: dict[str, Any]) -> 'NBTCompound[V]':
        if isinstance(obj, NBTCompound):
            return obj
        compound: dict[str, V] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError('Keys must be strings')
            compound[key] = NBT.from_object(value)  # type: ignore
        return cls(compound)

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def get(self, key: str, default: V | None = None) -> V | None:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        return self.value.get(key, default)

    def __getitem__(self, key: str) -> V:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        if key not in self.value:
            raise KeyError(f'Key {repr(key)} not found in NBTCompound')
        return self.value[key]

    def put(self, key: str, value: V) -> Self:
        if not isinstance(key, str):
            raise TypeError('Key must be a string')
        if not isinstance(value, NBT):
            raise ValueError('Value must be an NBT instance')
        self.value[key] = value
        return self


class NBTGenericArray[IT: NBT, OT](NBT[list[IT]]):
    item_type: type[IT]
    id_character: str

    def __init_subclass__(cls, item_type: type[IT], id_character: str) -> None:
        super().__init_subclass__()
        cls.item_type = item_type
        assert len(id_character) == 1, 'id_character must be a single character'
        cls.id_character = id_character

    def __init__(self, value: list[IT] | None = None) -> None:
        if value is None:
            value = []
        if not isinstance(value, list):
            raise TypeError('Value must be a list')
        for item in value:
            if not isinstance(item, self.item_type):
                raise ValueError(
                    f'All items must be {self.item_type.__name__} instances',
                )
        super().__init__(value)

    def into_snbt(self, indent: int | None = 4, level: int = 0) -> str:
        items = ','.join(item.into_snbt(None) for item in self.value)
        return f'[{self.id_character};{items}]'

    def into_object(self) -> list[OT]:
        return [item.into_object() for item in self.value]

    @classmethod
    def _parse_snbt(cls, s: str) -> tuple[Self, int]:
        prefix = f'[{cls.id_character};'
        if not s.startswith(prefix):
            raise ValueError(f'Invalid SNBT format for {cls.__name__}')
        offset = cls.skip_whitespace(s, len(prefix))
        items: list[IT] = []
        while True:
            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == ']':
                return cls(items), offset + 1

            item, length = cls.item_type._parse_snbt(s[offset:])
            items.append(item)
            offset = cls.skip_whitespace(s, offset + length)

            if offset >= len(s):
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            if s[offset] == ']':
                return cls(items), offset + 1
            if s[offset] != ',':
                raise ValueError(f'Invalid SNBT format for {cls.__name__}')
            offset = cls.skip_whitespace(s, offset + 1)

    @classmethod
    def from_object(cls, obj: Any) -> Self:
        if isinstance(obj, cls):
            return obj
        if not isinstance(obj, list):
            raise TypeError('Value must be a list')
        return cls([cls.item_type.from_object(item) for item in obj])  # type: ignore

    def __len__(self) -> int:
        return len(self.value)

    def is_empty(self) -> bool:
        return len(self.value) == 0

    def __getitem__(self, index: int) -> IT:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        return self.value[index]

    def __setitem__(self, index: int, value: IT) -> None:
        if not isinstance(index, int):
            raise TypeError('Index must be an integer')
        if not isinstance(value, self.item_type):
            raise ValueError(f'Value must be an instance of {self.item_type.__name__}')
        self.value[index] = value

    def append(self, value: IT) -> Self:
        if not isinstance(value, self.item_type):
            raise ValueError(f'Value must be an instance of {self.item_type.__name__}')
        self.value.append(value)
        return self


class NBTByteArray(NBTGenericArray[NBTByte, int], item_type=NBTByte, id_character='B'):
    pass


class NBTIntArray(NBTGenericArray[NBTInt, int], item_type=NBTInt, id_character='I'):
    pass


class NBTLongArray(NBTGenericArray[NBTLong, int], item_type=NBTLong, id_character='L'):
    pass


# Order matters: a suffixed number must be tried before the unsuffixed types whose
# regex would otherwise match a prefix of it, and `1b` is a byte while `true` is not.
PARSE_ORDER: tuple[type[NBT], ...] = (
    NBTByte,
    NBTBoolean,
    NBTShort,
    NBTLong,
    NBTFloat,
    NBTDouble,
    NBTInt,
    NBTString,
    NBTByteArray,
    NBTIntArray,
    NBTLongArray,
    NBTList,
    NBTCompound,
)
