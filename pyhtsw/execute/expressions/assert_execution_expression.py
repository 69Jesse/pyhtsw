from collections.abc import Callable
from typing import TYPE_CHECKING, NoReturn, Self

from pyhtsw.clone import MISSING, Missing, clone_with
from pyhtsw.execute.exception import descriptive_backend_type
from pyhtsw.execute.expressions.execution_expression import ExecutionExpression
from pyhtsw.expression.condition.condition import Condition
from pyhtsw.expression.condition.conditional_expression import ConditionalMode
from pyhtsw.utils.callback import call_with_optional_arg

if TYPE_CHECKING:
    from pyhtsw.execute.house import EmulatedHouse


__all__ = ('AssertExecutionExpression',)


class AssertExecutionExpression(ExecutionExpression):
    conditions: tuple[
        Condition
        | Callable[[], Condition | None]
        | Callable[['EmulatedHouse'], Condition | None],
        ...,
    ]
    mode: ConditionalMode
    message: str | None

    def __init__(
        self,
        conditions: tuple[
            Condition
            | Callable[[], Condition | None]
            | Callable[['EmulatedHouse'], Condition | None],
            ...,
        ],
        *,
        mode: ConditionalMode,
        message: str | None = None,
    ) -> None:
        self.conditions = conditions
        self.mode = mode
        self.message = message

    def cloned(
        self,
        *,
        conditions: tuple[
            Condition
            | Callable[[], Condition | None]
            | Callable[['EmulatedHouse'], Condition | None],
            ...,
        ]
        | Missing = MISSING,
        mode: ConditionalMode | Missing = MISSING,
        message: str | None | Missing = MISSING,
    ) -> Self:
        return clone_with(
            self,
            {
                'conditions': conditions,
                'mode': mode,
                'message': message,
            },
        )

    def equals(self, other: object) -> bool:
        if not isinstance(other, AssertExecutionExpression):
            return False
        if self.mode != other.mode:
            return False
        if len(self.conditions) != len(other.conditions):
            return False
        return all(
            self.conditions[i].equals(other.conditions[i])  # type: ignore
            if not callable(self.conditions[i]) and not callable(other.conditions[i])
            else self.conditions[i] == other.conditions[i]
            if callable(self.conditions[i]) and callable(other.conditions[i])
            else False
            for i in range(len(self.conditions))
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(conditions={self.conditions!r}, mode={self.mode!r})'

    def throw(
        self,
        context: 'EmulatedHouse',
        *,
        failed_conditions: list['Condition'],
    ) -> NoReturn:
        from pyhtsw.checkable import Checkable

        assert len(failed_conditions) > 0

        message = (
            f'"{context.get(self.message, output="string")}": ' if self.message else ''
        )
        if self.mode is ConditionalMode.ALL:
            assert len(failed_conditions) == 1
            middle = 'The following condition did not hold: '
        else:
            middle = 'None of the following conditions held: '

        def descriptive_condition(cond: 'Condition') -> str:
            return f'{" " * 4}{cond!r}\n' + '\n'.join(
                f'{" " * 8}{part!r}: {descriptive_backend_type(context.get(part, output="backend"))}'
                for part in cond.related_debug_parts()
                if isinstance(part, Checkable)
            )

        raise AssertionError(
            f'{message}{middle}\n'
            + '\n'.join(map(descriptive_condition, failed_conditions)),
        )

    def flattened_conditions(self, context: 'EmulatedHouse') -> list['Condition']:
        flattened: list[Condition] = []
        for cond in self.conditions:
            if callable(cond):
                cond = call_with_optional_arg(cond, context, noun='conditions')
                if cond is None:
                    continue
            if isinstance(cond, AssertExecutionExpression) and cond.mode == self.mode:
                flattened.extend(cond.flattened_conditions(context))
            else:
                flattened.append(cond)  # type: ignore
        return flattened

    def raw_execute(self, context: 'EmulatedHouse') -> None:
        conditions = self.flattened_conditions(context)
        if self.mode == ConditionalMode.ALL:
            for condition in conditions:
                if not condition.evaluate(context):
                    self.throw(context, failed_conditions=[condition])
        elif self.mode == ConditionalMode.ANY:
            for condition in conditions:
                if condition.evaluate(context):
                    return
            self.throw(context, failed_conditions=conditions)
