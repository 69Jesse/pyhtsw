from pyhtsw.nbt import (
    NBT,
    NBTBoolean,
    NBTByte,
    NBTByteArray,
    NBTCompound,
    NBTDouble,
    NBTFloat,
    NBTInt,
    NBTIntArray,
    NBTList,
    NBTLong,
    NBTLongArray,
    NBTShort,
    NBTString,
)


def parses_as(snbt: str, cls: type[NBT], value: object) -> None:
    nbt = NBT.from_snbt(snbt)
    assert type(nbt) is cls, (
        f'{snbt!r}: expected {cls.__name__}, got {type(nbt).__name__}'
    )
    assert nbt.into_object() == value, (
        f'{snbt!r}: expected {value!r}, got {nbt.into_object()!r}'
    )


def rejects(snbt: str) -> None:
    try:
        NBT.from_snbt(snbt)
    except ValueError:
        return
    raise AssertionError(f'{snbt!r} should not have parsed')


# === Every scalar type dispatches to itself, suffix or not ===
parses_as('1b', NBTByte, 1)
parses_as('-128b', NBTByte, -128)
parses_as('true', NBTBoolean, True)
parses_as('false', NBTBoolean, False)
parses_as('1s', NBTShort, 1)
parses_as('1l', NBTLong, 1)
parses_as('1000000000000l', NBTLong, 1000000000000)
parses_as('-2.5f', NBTFloat, -2.5)
parses_as('1.5d', NBTDouble, 1.5)
parses_as('1.5', NBTDouble, 1.5)  # unsuffixed decimal is a double, not a truncated int
parses_as('.5', NBTDouble, 0.5)
parses_as('1', NBTInt, 1)  # ... but a bare integer stays an int
parses_as('-42', NBTInt, -42)
parses_as('"hi"', NBTString, 'hi')
parses_as("'hi'", NBTString, 'hi')


# === Whitespace is allowed between every token ===
parses_as('{a: 1}', NBTCompound, {'a': 1})
parses_as('{ a : 1 }', NBTCompound, {'a': 1})
parses_as('  {a:1}  \n', NBTCompound, {'a': 1})  # incl. a trailing newline
parses_as('[1, 2]', NBTList, [1, 2])
parses_as('[\n    1,\n    2\n]', NBTList, [1, 2])
parses_as('[B; 1b, 2b]', NBTByteArray, [1, 2])
parses_as('{\n    a: [\n        {b: 1s}\n    ]\n}', NBTCompound, {'a': [{'b': 1}]})


# === Typed arrays are reachable from the generic parser ===
parses_as('[B;1b,2b]', NBTByteArray, [1, 2])
parses_as('[I;1,2]', NBTIntArray, [1, 2])
parses_as('[L;1l]', NBTLongArray, [1])
parses_as('[B;]', NBTByteArray, [])


# === Containers, empty and nested ===
parses_as('{}', NBTCompound, {})
parses_as('[]', NBTList, [])
parses_as('[0:1,1:2]', NBTList, [1, 2])  # indexed list form
parses_as('{"a:b": 1}', NBTCompound, {'a:b': 1})  # quoted key containing a delimiter
parses_as('{a-b.c+d: 1}', NBTCompound, {'a-b.c+d': 1})  # non-identifier key


# === String escapes survive a round trip ===
parses_as(r'"x\"y"', NBTString, 'x"y')
parses_as(r'"back\\slash"', NBTString, 'back\\slash')
parses_as(r"'say \'hi\''", NBTString, "say 'hi'")
assert NBTString('x"y').into_snbt() == r'"x\"y"'
assert NBTString('back\\slash').into_snbt() == r'"back\\slash"'
for text in ('x"y', 'back\\slash', 'both \\" here', '§4§lADMIN BOW'):
    assert NBT.from_snbt(NBTString(text).into_snbt()).into_object() == text


# === E notation is accepted but never written ===
parses_as('1.0E-7', NBTDouble, 1e-07)
parses_as('1.5e3f', NBTFloat, 1500.0)
parses_as('2e3', NBTDouble, 2000.0)
parses_as('-1.2E+2d', NBTDouble, -120.0)
assert 'e' not in NBTDouble(1e-07).into_snbt().lower()
# A bare int must still parse as an int, not get swallowed by the double branch.
parses_as('7', NBTInt, 7)


# === Malformed input raises ValueError, never IndexError ===
rejects('{a:1')
rejects('[1,2')
rejects('[B;1b')
rejects('"unterminated')
rejects('{a:1}}')
rejects('1 2')
rejects('{a:1,b}')
rejects('{a:1 b:2}')
rejects('{a:1,a:2}')  # duplicate key
rejects('')


# === A pretty-printed item round trips byte for byte ===
ITEM_SNBT = """{
    id: "minecraft:bow",
    Count: 1b,
    tag: {
        ench: [
            {
                lvl: 1s,
                id: 7s
            }
        ],
        HideFlags: 1,
        display: {
            Lore: [
                "§7Power X",
                "§9Unbreakable"
            ],
            Name: "§4§lADMIN BOW"
        },
        ExtraAttributes: {
            interact_data: {
                data: "Rv1amAU3+8wLyNQ/Difjia6==",
                version: 2
            }
        }
    },
    Damage: 0s
}"""

item = NBT.from_snbt(ITEM_SNBT)
assert item.into_snbt(indent=4) == ITEM_SNBT
assert isinstance(item, NBTCompound)
assert item['Count'].into_object() == 1
assert item['tag']['display']['Name'].into_object() == '§4§lADMIN BOW'
assert item['tag']['ExtraAttributes']['interact_data']['version'].into_object() == 2
assert NBT.from_snbt(item.into_snbt(indent=None)).into_object() == item.into_object()
minified = item.into_snbt(indent=None)
assert '\n' not in minified, minified  # indent=None must reach nested children too
assert NBT.from_snbt('{a:[{b:1s}],c:[I;1,2]}').into_snbt(indent=None) == (
    '{a:[{b:1s}],c:[I;1,2]}'
)


# === from_object builds lists out of plain Python values ===
assert NBT.from_object([1, 2]).into_object() == [1, 2]
assert NBT.from_object({'a': [1]}).into_object() == {'a': [1]}
assert NBTIntArray.from_object([1, 2]).into_snbt() == '[I;1,2]'
assert isinstance(NBT.from_object(NBTList([NBTInt(1)])), NBTList)
