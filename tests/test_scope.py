from helpers import expect_exception

from pyhtsw import (
    Container,
    GlobalStat,
    IfAll,
    Item,
    Random,
    cancel_event,
    close_menu,
    consume_item,
    event,
    exit_function,
    function,
    kill_player,
    send_to_lobby,
)
from pyhtsw.compiler.scope import ScopeError

flag = GlobalStat('flag').as_long()


with expect_exception(ScopeError):
    with Container():

        def _conditional_in_item() -> None:
            with IfAll(flag == 1):
                flag.value = 2

        Item('paper', name='Bad', on_right_click=_conditional_in_item)


with expect_exception(ScopeError):
    with Container():

        def _random_in_item() -> None:
            with Random:
                flag.value = 1
                flag.value = 2

        Item('paper', name='Bad', on_right_click=_random_in_item)


with Container():

    def _plain_in_item() -> None:
        flag.value = 1
        consume_item()

    Item('paper', name='Good', on_right_click=_plain_in_item)


with expect_exception(ScopeError):
    with Container():

        @function('Cancels')
        def _cancel_in_function() -> None:
            with IfAll(flag == 1):
                cancel_event()


with expect_exception(ScopeError):
    with Container():

        @event('Player Join')
        def _cancel_in_uncancellable() -> None:
            with IfAll(flag == 1):
                cancel_event()


with Container():

    @event('Player Damage')
    def _cancel_in_cancellable() -> None:
        with IfAll(flag == 1):
            cancel_event()


with expect_exception(ScopeError):
    with Container():

        @event('Player Join')
        def _kill_in_event() -> None:
            with IfAll(flag == 1):
                kill_player()


with expect_exception(ScopeError):
    with Container():

        @event('Player Join')
        def _lobby_in_event() -> None:
            with IfAll(flag == 1):
                send_to_lobby('Housing')


with expect_exception(ScopeError):
    with Container():
        from pyhtsw import chat

        @event('Player Quit')
        def _chat_on_quit() -> None:
            chat('bye')


with Container():

    @event('Player Quit')
    def _var_on_quit() -> None:
        flag.value = 1


with expect_exception(ScopeError):
    with Container():
        from pyhtsw import Group, change_player_group

        group = Group('Loop')

        @event('Group Change')
        def _regroup() -> None:
            change_player_group(group)


with expect_exception(ScopeError):
    with Container():

        @function('Consumes')
        def _consume_in_function() -> None:
            consume_item()


with expect_exception(ScopeError):
    with Container():

        @function('Closes')
        def _close_in_function() -> None:
            close_menu()


with expect_exception(ScopeError):
    with Container():
        from pyhtsw import DamageCause

        @function('Wrong Context')
        def _damage_cause_in_function() -> None:
            with IfAll(DamageCause('Fall')):
                flag.value = 1


with Container():
    from pyhtsw import DamageCause as _DamageCause

    @event('Player Damage')
    def _damage_cause_in_event() -> None:
        with IfAll(_DamageCause('Fall')):
            flag.value = 1


with expect_exception(ScopeError):
    with Container():

        @function('Exits')
        def _exit_at_top_level() -> None:
            exit_function()


with Container():

    @function('Exits Guarded')
    def _exit_in_conditional() -> None:
        with IfAll(flag == 1):
            exit_function()
