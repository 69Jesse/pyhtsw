from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhtsw.limits import ImportableKind

    from pyhtsw.expression.condition.condition import Condition
    from pyhtsw.expression.condition.conditional_expression import ConditionalExpression
    from pyhtsw.expression.expression import Expression


__all__ = ('simplify_expressions',)


def _same_condition_set(left: list['Condition'], right: list['Condition']) -> bool:
    if len(left) != len(right):
        return False
    unmatched = list(right)
    for condition in left:
        for index, other in enumerate(unmatched):
            if condition.equals(other):
                del unmatched[index]
                break
        else:
            return False
    return True


def _can_merge(
    first: 'ConditionalExpression',
    second: 'ConditionalExpression',
) -> bool:
    from pyhtsw.schedule import body_writes, conditions_read

    if first.mode is not second.mode:
        return False
    if not _same_condition_set(first.conditions, second.conditions):
        return False

    reads = conditions_read(first.conditions)
    if reads is None:
        return False
    # A barrier in the first body puts the second check out of reach entirely.
    writes = body_writes(first)
    if writes is None:
        return False
    # Running the first body must not be able to flip the check the second one
    # is about to make.
    return not (writes & reads)


def _merge_conditionals(
    expressions: list['Expression'],
    *,
    importable: 'ImportableKind',
) -> bool:
    from pyhtsw.limits import is_within_limits

    from pyhtsw.expression.condition.conditional_expression import ConditionalExpression

    has_changed = False
    index = 0
    while index < len(expressions) - 1:
        first = expressions[index]
        second = expressions[index + 1]
        if not (
            isinstance(first, ConditionalExpression)
            and isinstance(second, ConditionalExpression)
            and _can_merge(first, second)
        ):
            index += 1
            continue

        merged_if = first.if_expressions + second.if_expressions
        merged_else = first.else_expressions + second.else_expressions
        # A merged body still has to fit the container it lands in; a merge that
        # only moves the overflow one level down is no merge at all.
        if not is_within_limits(
            merged_if,
            importable=importable,
            nested='conditional',
        ) or not is_within_limits(
            merged_else,
            importable=importable,
            nested='conditional',
        ):
            index += 1
            continue

        first.if_expressions = merged_if
        first.else_expressions = merged_else
        del expressions[index + 1]
        has_changed = True

    return has_changed


def _drop_unreachable(expressions: list['Expression']) -> bool:
    from pyhtsw.actions.exit_function import ExitFunctionExpression

    for index, expression in enumerate(expressions):
        if isinstance(expression, ExitFunctionExpression) and index + 1 < len(
            expressions,
        ):
            del expressions[index + 1 :]
            return True
    return False


def _drop_empty_conditionals(expressions: list['Expression']) -> bool:
    from pyhtsw.expression.condition.conditional_expression import ConditionalExpression

    has_changed = False
    for index in range(len(expressions) - 1, -1, -1):
        expression = expressions[index]
        if (
            isinstance(expression, ConditionalExpression)
            and not expression.conditions
            and not expression.if_expressions
            and not expression.else_expressions
        ):
            del expressions[index]
            has_changed = True
    return has_changed


def simplify_expressions(
    expressions: list['Expression'],
    *,
    importable: 'ImportableKind' = 'functions',
) -> bool:
    """Merge conditionals that check the same thing and drop what cannot run.
    Recurses into nested action lists first, so an inner merge is visible to the
    limit check an outer merge makes."""
    from pyhtsw.actions.no_optimization import optimization_enabled

    from pyhtsw.expression.binary_expression import BinaryExpression

    has_changed = False
    for expression in expressions:
        for body in expression.nested_expressions_refs():
            has_changed |= simplify_expressions(body, importable=importable)

    if optimization_enabled('dead_code'):
        has_changed |= _drop_unreachable(expressions)
        has_changed |= _drop_empty_conditionals(expressions)

    if optimization_enabled('merge_conditionals'):
        merged = _merge_conditionals(expressions, importable=importable)
        if merged:
            has_changed = True
            # Joining two bodies puts previously separated writes next to each
            # other, which the peephole passes can now collapse.
            for expression in expressions:
                for body in expression.nested_expressions_refs():
                    BinaryExpression.optimize_binary_expressions(body)

    return has_changed
