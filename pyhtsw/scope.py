from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .block import Block
    from .expression.expression import Expression
    from .importable import Importable
    from .limits import ImportableKind

__all__ = (
    'ScopeError',
    'ScopeViolation',
    'check_scopes',
)


class ScopeError(RuntimeError):
    """An action was written into a container that cannot hold it."""


class ScopeViolation(NamedTuple):
    where: str
    message: str


CANCELLABLE_EVENTS: frozenset[str] = frozenset(
    {
        'Player Death',
        'Fish Caught',
        'Player Damage',
        'Player Drop Item',
        'Player Pick Up Item',
        'Player Change Held Item',
        'Player Toggle Sneak',
        'Player Toggle Flight',
    },
)

_TABLES: 'dict[str, object] | None' = None


def _tables() -> 'dict[str, object]':
    global _TABLES
    if _TABLES is not None:
        return _TABLES

    from .actions.apply_inventory_layout import ApplyInventoryLayoutExpression
    from .actions.apply_potion_effect import ApplyPotionEffectExpression
    from .actions.block_type import BlockType
    from .actions.can_pvp import CanPVPCondition
    from .actions.cancel_event import CancelEventExpression
    from .actions.change_player_group import ChangePlayerGroupExpression
    from .actions.change_velocity import ChangeVelocityExpression
    from .actions.chat import ChatExpression
    from .actions.clear_potion_effects import ClearPotionEffectsExpression
    from .actions.close_menu import CloseMenuExpression
    from .actions.consume_item import ConsumeItemExpression
    from .actions.damage_amount import DamageAmountCondition
    from .actions.damage_cause import DamageCause
    from .actions.display_action_bar import DisplayActionBarExpression
    from .actions.display_menu import DisplayMenuExpression
    from .actions.display_title import DisplayTitleExpression
    from .actions.drop_item import DropItemExpression
    from .actions.enchant_held_item import EnchantHeldItemExpression
    from .actions.exit_function import ExitFunctionExpression
    from .actions.fail_parkour import FailParkourExpression
    from .actions.fishing_environment import FishingEnvironment
    from .actions.full_heal import FullHealExpression
    from .actions.give_experience_levels import GiveExperienceLevelsExpression
    from .actions.give_item import GiveItemExpression
    from .actions.is_item import IsItem
    from .actions.kill_player import KillPlayerExpression
    from .actions.launch_to_target import LaunchToTargetExpression
    from .actions.parkour_checkpoint import ParkourCheckpointExpression
    from .actions.play_sound import PlaySoundExpression
    from .actions.player_health import PlayerHealthPlaceholder
    from .actions.player_hunger import PlayerHungerPlaceholder
    from .actions.player_max_health import PlayerMaxHealthPlaceholder
    from .actions.portal_type import PortalType
    from .actions.random import RandomExpression
    from .actions.remove_item import RemoveItemExpression
    from .actions.reset_inventory import ResetInventoryExpression
    from .actions.send_to_lobby import SendToLobbyExpression
    from .actions.set_compass_target import SetCompassTargetExpression
    from .actions.set_gamemode import SetGamemodeExpression
    from .actions.set_player_team import SetPlayerTeamExpression
    from .actions.set_player_time import SetPlayerTimeExpression
    from .actions.set_player_weather import SetPlayerWeatherExpression
    from .actions.teleport_player import TeleportPlayerExpression
    from .actions.toggle_nametag_display import ToggleNametagDisplayExpression
    from .expression.condition.conditional_expression import ConditionalExpression

    condition_names = {
        BlockType: 'Block Type',
        CanPVPCondition: 'Can PvP',
        DamageAmountCondition: 'Damage Amount',
        DamageCause: 'Damage Cause',
        FishingEnvironment: 'Fishing Environment',
        IsItem: 'Is Item',
        PortalType: 'Portal Type',
    }

    names = {
        ApplyInventoryLayoutExpression: 'Apply Inventory Layout',
        ApplyPotionEffectExpression: 'Apply Potion Effect',
        CancelEventExpression: 'Cancel Event',
        ChangePlayerGroupExpression: "Change Player's Group",
        ChangeVelocityExpression: 'Change Velocity',
        ChatExpression: 'Send a Chat Message',
        ClearPotionEffectsExpression: 'Clear All Potion Effects',
        CloseMenuExpression: 'Close Menu',
        ConditionalExpression: 'Conditional',
        ConsumeItemExpression: 'Use/Remove Held Item',
        DisplayActionBarExpression: 'Display Action Bar',
        DisplayMenuExpression: 'Display Menu',
        DisplayTitleExpression: 'Display Title',
        DropItemExpression: 'Drop Item',
        EnchantHeldItemExpression: 'Enchant Held Item',
        ExitFunctionExpression: 'Exit',
        FailParkourExpression: 'Fail Parkour',
        FullHealExpression: 'Full Heal',
        GiveExperienceLevelsExpression: 'Give Experience Levels',
        GiveItemExpression: 'Give Item',
        KillPlayerExpression: 'Kill Player',
        LaunchToTargetExpression: 'Launch to Target',
        ParkourCheckpointExpression: 'Parkour Checkpoint',
        PlaySoundExpression: 'Play Sound',
        PlayerHealthPlaceholder: 'Change Health',
        PlayerHungerPlaceholder: 'Change Hunger Level',
        PlayerMaxHealthPlaceholder: 'Change Max Health',
        RandomExpression: 'Random Action',
        RemoveItemExpression: 'Remove Item',
        ResetInventoryExpression: 'Reset Inventory',
        SendToLobbyExpression: 'Send to Lobby',
        SetCompassTargetExpression: 'Set Compass Target',
        SetGamemodeExpression: 'Set Gamemode',
        SetPlayerTeamExpression: 'Set Player Team',
        SetPlayerTimeExpression: 'Set Player Time',
        SetPlayerWeatherExpression: 'Set Player Weather',
        TeleportPlayerExpression: 'Teleport Player',
        ToggleNametagDisplayExpression: 'Toggle Nametag Display',
    }

    _TABLES = {
        'names': names,
        'nestable': frozenset({ConditionalExpression, RandomExpression}),
        'cancel_event': CancelEventExpression,
        'exit': ExitFunctionExpression,
        'item_only': {ConsumeItemExpression: 'Use/Remove Held Item'},
        'menu_only': {CloseMenuExpression: 'Close Menu'},
        'all_events_forbidden': frozenset(
            {
                KillPlayerExpression,
                SendToLobbyExpression,
            },
        ),
        'event_forbidden': {
            'Player Quit': frozenset(
                {
                    ChangePlayerGroupExpression,
                    FullHealExpression,
                    DisplayTitleExpression,
                    DisplayActionBarExpression,
                    ResetInventoryExpression,
                    PlayerMaxHealthPlaceholder,
                    ParkourCheckpointExpression,
                    GiveItemExpression,
                    RemoveItemExpression,
                    ChatExpression,
                    ApplyPotionEffectExpression,
                    ClearPotionEffectsExpression,
                    GiveExperienceLevelsExpression,
                    TeleportPlayerExpression,
                    FailParkourExpression,
                    PlaySoundExpression,
                    SetCompassTargetExpression,
                    SetGamemodeExpression,
                    PlayerHealthPlaceholder,
                    PlayerHungerPlaceholder,
                    ApplyInventoryLayoutExpression,
                    EnchantHeldItemExpression,
                    SetPlayerTeamExpression,
                    DisplayMenuExpression,
                    DropItemExpression,
                    ChangeVelocityExpression,
                    LaunchToTargetExpression,
                    SetPlayerWeatherExpression,
                    SetPlayerTimeExpression,
                    ToggleNametagDisplayExpression,
                },
            ),
            'Group Change': frozenset({ChangePlayerGroupExpression}),
        },
        'condition_names': condition_names,
        'event_scoped_conditions': {
            DamageAmountCondition: ('Player Damage',),
            DamageCause: ('Player Damage',),
            CanPVPCondition: ('PvP State Change',),
            FishingEnvironment: ('Fish Caught',),
            PortalType: ('Player Enter Portal',),
            BlockType: ('Player Block Break',),
            IsItem: (
                'Player Drop Item',
                'Player Pick Up Item',
                'Player Change Held Item',
            ),
        },
    }
    return _TABLES


def _name(cls: object) -> str:
    names: dict = _tables()['names']  # type: ignore[assignment]
    return names.get(cls, getattr(cls, '__name__', str(cls)))


def _check_conditions(
    expression: 'Expression',
    *,
    event: str | None,
    report: 'list[str]',
) -> None:
    from .expression.condition.conditional_expression import ConditionalExpression

    if not isinstance(expression, ConditionalExpression):
        return

    tables = _tables()
    scoped: dict = tables['event_scoped_conditions']  # type: ignore[assignment]
    condition_names: dict = tables['condition_names']  # type: ignore[assignment]

    for condition in expression.conditions:
        allowed = scoped.get(type(condition))
        if allowed is None or (event is not None and event in allowed):
            continue
        name = condition_names.get(type(condition), type(condition).__name__)
        context = f'{event} event' if event else 'this context'
        report.append(
            f'{name} condition can only be used inside: '
            f'{", ".join(allowed)}. It cannot be used in {context}.',
        )


def _check_action(
    cls: object,
    *,
    kind: 'ImportableKind',
    event: str | None,
    nested: bool,
    report: 'list[str]',
) -> None:
    tables = _tables()

    if kind == 'items' and cls in tables['nestable']:  # type: ignore[operator]
        report.append(f'{_name(cls)} action cannot be used inside items')

    if cls is tables['cancel_event']:
        if kind != 'events':
            report.append(f'Cancel Event action cannot be used inside {kind}')
        elif event is not None and event not in CANCELLABLE_EVENTS:
            report.append(f'{event} event cannot be cancelled.')

    item_only: dict = tables['item_only']  # type: ignore[assignment]
    if cls in item_only and kind != 'items':
        report.append(
            f'{item_only[cls]} action can only be used inside items, not {kind}',
        )

    menu_only: dict = tables['menu_only']  # type: ignore[assignment]
    if cls in menu_only and kind != 'menus':
        report.append(
            f'{menu_only[cls]} action can only be used inside menus, not {kind}',
        )

    if cls is tables['exit'] and not nested:
        report.append(
            'Exit action can only be used inside conditional or random actions',
        )

    if kind == 'events':
        if cls in tables['all_events_forbidden']:  # type: ignore[operator]
            report.append(f'{_name(cls)} action cannot be used inside events')
        event_forbidden: dict = tables['event_forbidden']  # type: ignore[assignment]
        if event is not None and cls in event_forbidden.get(event, frozenset()):
            report.append(
                f'{_name(cls)} action cannot be used inside {event} events',
            )


def _walk(
    expressions: 'list[Expression]',
    *,
    kind: 'ImportableKind',
    event: str | None,
    nested: bool,
    report: 'list[str]',
) -> None:
    from .limits import Counter, nesting_of

    counter = Counter(importable=kind)
    for expression in expressions:
        for cls in counter.action_counts(expression):
            _check_action(
                cls,
                kind=kind,
                event=event,
                nested=nested,
                report=report,
            )
        _check_conditions(expression, event=event, report=report)
        inner_nested = nested or nesting_of(expression) is not None
        for inner in expression.nested_expressions_refs():
            _walk(
                inner,
                kind=kind,
                event=event,
                nested=inner_nested,
                report=report,
            )


def check_scopes(
    blocks: 'list[Block]',
    importables: 'list[Importable]',
) -> list[ScopeViolation]:
    from .importable import EventImportable

    events_by_block: dict[int, str] = {
        id(importable.block): importable.event
        for importable in importables
        if isinstance(importable, EventImportable)
    }

    violations: list[ScopeViolation] = []
    for block in blocks:
        report: list[str] = []
        _walk(
            block.expressions,
            kind=block.importable_kind,
            event=events_by_block.get(id(block)),
            nested=False,
            report=report,
        )
        if not report:
            continue
        where = f'{block.importable_kind[:-1]} "{block.get_name()}"'
        for message in dict.fromkeys(report):
            violations.append(ScopeViolation(where, message))
    return violations


def raise_scope_violations(violations: list[ScopeViolation]) -> None:
    if not violations:
        return
    lines = [f'  - {violation.where}: {violation.message}' for violation in violations]
    raise ScopeError(
        'These actions are not allowed in the container they were written into:\n'
        + '\n'.join(lines),
    )
