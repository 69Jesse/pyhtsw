from pyhtsw import (
    Container,
    GlobalStat,
    IfAll,
    Item,
    cancel_event,
    event,
    exit_function,
    function,
    pause_execution,
    send_to_lobby,
    trigger_function,
)


def emit(guard, event_name: str | None = None) -> str:
    with Container() as container:
        flag = GlobalStat('flag').as_long()
        other = GlobalStat('other').as_long()

        def body() -> None:
            flag.value = 0
            with IfAll(other == 1):
                guard()
            flag.value = 1

        # `cancel_event` is only legal inside a cancellable event, so that case
        # needs a real event container rather than a bare block.
        if event_name is None:
            body()
        else:
            event(event_name)(body)
    return container.into_htsl()


with Container() as helper_container:

    @function('Helper', icon=Item('paper'))
    def helper() -> None:
        pass


for name, guard, event_name in (
    ('exit', exit_function, None),
    ('lobby', lambda: send_to_lobby('Housing'), None),
    ('cancel', cancel_event, 'Player Damage'),
    ('pause', lambda: pause_execution(1), None),
    ('trigger', lambda: trigger_function(helper), None),
):
    htsl = emit(guard, event_name)
    assert 'globalvar "flag" = 0' in htsl, (name, htsl)
    assert 'globalvar "flag" = 1' in htsl, (name, htsl)

with Container() as container:
    flag = GlobalStat('flag').as_long()
    flag.value = 0
    flag.value = 1

assert container.into_htsl() == 'globalvar "flag" = 1 true', container.into_htsl()
