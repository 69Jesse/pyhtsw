import json
from pathlib import Path

from pyhtsw.importable import (
    EVENTS,
    CommandImportable,
    EventImportable,
    FunctionImportable,
    GroupImportable,
    ItemImportable,
    MenuImportable,
    NpcImportable,
    RegionImportable,
    TeamImportable,
)
from pyhtsw.limits import (
    EVENT_CONDITIONAL_LIMIT,
    RANDOM_FLOOR,
    get_limit,
    get_limits,
)
from pyhtsw.types import (
    ALL_CHAT_SPEEDS,
    ALL_COMMAND_MODES,
    ALL_DEFAULT_GAMEMODES,
    ALL_HOUSING_COLORS,
    ALL_PERMISSIONS,
)

CONTRACT = json.loads(
    (Path(__file__).parent / 'htsw_contract.json').read_text(encoding='utf-8'),
)


def literal_values(alias: object) -> tuple[str, ...]:
    return alias.__args__  # type: ignore[attr-defined]


enums = CONTRACT['enums']
assert list(EVENTS) == enums['events'], EVENTS
assert list(literal_values(ALL_HOUSING_COLORS)) == enums['colors']
assert list(literal_values(ALL_CHAT_SPEEDS)) == enums['chatSpeeds']
assert list(literal_values(ALL_DEFAULT_GAMEMODES)) == enums['defaultGameModes']
assert list(literal_values(ALL_COMMAND_MODES)) == enums['commandModes']
assert list(literal_values(ALL_PERMISSIONS)) == enums['permissions']

# EventName mirrors EVENTS; keep the two in step.
from pyhtsw.importable import EventName, NpcSkin  # noqa: E402

assert list(literal_values(EventName)) == enums['events']
assert list(literal_values(NpcSkin)) == enums['npcSkins']


IMPORTABLES = (
    FunctionImportable,
    EventImportable,
    RegionImportable,
    ItemImportable,
    MenuImportable,
    TeamImportable,
    GroupImportable,
    CommandImportable,
    NpcImportable,
)
assert {cls.kind for cls in IMPORTABLES} == set(CONTRACT['importables']), (
    'pyhtsw does not cover every htsw importable: '
    f'{set(CONTRACT["importables"]) - {cls.kind for cls in IMPORTABLES}}'
)


# htsw takes an NPC's `pos` as its identity and matches on the exact `x,y,z`
# string, so a fraction can never name a live NPC. Both sides reject it.
assert all(CONTRACT['nested']['pos'][axis].get('integer') for axis in 'xyz')

for importable, kwargs in (
    (NpcImportable, {'name': 'Guide', 'pos': (1.5, 64, -2)}),
    (RegionImportable, {'name': 'Spawn', 'bounds': ((0, 64, 0), (4, 68.25, 4))}),
):
    try:
        importable(**kwargs).build(None)  # type: ignore[arg-type]
    except ValueError as error:
        assert 'must be a whole number' in str(error), error
    else:
        raise AssertionError(f'{importable.__name__} accepted a fractional coordinate')


from pyhtsw.registry import (  # noqa: E402
    iter_action_types,
    iter_condition_types,
    iter_placeholder_types,
)


def registered_limits(classes) -> dict[str, int]:
    limits: dict[str, int] = {}
    for cls in classes:
        meta = cls.__dict__.get('htsw_meta')
        if meta is None or meta.limit is None:
            continue
        assert meta.htsw_name is not None, (
            f'{cls.__name__} has a limit but no htsw_name'
        )
        previous = limits.setdefault(meta.htsw_name, meta.limit)
        assert previous == meta.limit, (
            f'{meta.htsw_name}: conflicting limits {previous} and {meta.limit}'
        )
    return limits


ours = registered_limits({*iter_action_types(), *iter_placeholder_types()})
assert set(get_limits()) == {
    cls
    for cls in {*iter_action_types(), *iter_placeholder_types()}
    if cls.__dict__.get('htsw_meta') is not None
    and cls.__dict__['htsw_meta'].limit is not None
}
theirs = CONTRACT['actionLimits']

missing = set(theirs) - set(ours)
assert not missing, f'htsw limits pyhtsw does not model: {sorted(missing)}'
extra = set(ours) - set(theirs)
assert not extra, f'pyhtsw limits htsw does not have: {sorted(extra)}'
for name in sorted(theirs):
    assert ours[name] == theirs[name], (
        f'{name}: pyhtsw has {ours[name]}, htsw has {theirs[name]}'
    )


from pyhtsw.actions.full_heal import FullHealExpression  # noqa: E402

from pyhtsw.expression.condition.conditional_expression import (  # noqa: E402
    ConditionalExpression,
)

context = CONTRACT['contextLimits']
assert (
    get_limit(ConditionalExpression, importable='events')
    == context['CONDITIONAL@events']
    == EVENT_CONDITIONAL_LIMIT
)
assert (
    get_limit(ConditionalExpression, importable='functions')
    == context['CONDITIONAL@functions']
)
assert (
    get_limit(ConditionalExpression, importable='events', nested='random')
    == context['CONDITIONAL@events/random']
)
assert (
    get_limit(FullHealExpression, importable='functions', nested='random')
    == context['HEAL@functions/random']
    == RANDOM_FLOOR
)


from pyhtsw.actions.has_potion_effect import HasPotionEffect  # noqa: E402
from pyhtsw.actions.is_doing_parkour import IsDoingParkourCondition  # noqa: E402
from pyhtsw.limits import (  # noqa: E402
    COMPARISON_LIMIT,
    get_condition_limit,
)

condition_limits = CONTRACT['conditionLimits']
assert (
    get_condition_limit(IsDoingParkourCondition) == condition_limits['IS_DOING_PARKOUR']
)
assert get_condition_limit(HasPotionEffect) == condition_limits['REQUIRE_POTION_EFFECT']
assert COMPARISON_LIMIT == condition_limits['COMPARE_VAR']

# Every non-comparison htsw condition type should be modelled; the COMPARE_*
# family is bucketed by lhs instead of by class.
COMPARISON_TYPES = {
    'COMPARE_VAR',
    'COMPARE_HEALTH',
    'COMPARE_MAX_HEALTH',
    'COMPARE_HUNGER',
    'COMPARE_PLACEHOLDER',
}
cond_ours = registered_limits(iter_condition_types())
cond_theirs = {
    name: limit
    for name, limit in condition_limits.items()
    if name not in COMPARISON_TYPES
}
assert cond_ours == cond_theirs, set(cond_ours.items()) ^ set(cond_theirs.items())
