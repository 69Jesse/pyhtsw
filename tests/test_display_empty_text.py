from pyhtsw import (
    Container,
    DisplayTitleExpression,
    display_action_bar,
    display_title,
)

# An empty title and an omitted subtitle both fall back to the reset code
with Container() as container:
    display_title('')

assert container.into_htsl() == 'title "&r" "&r" 1 5 1', container.into_htsl()


# Only the empty field is replaced
with Container() as container:
    display_title('&aHello', '')

assert container.into_htsl() == 'title "&aHello" "&r" 1 5 1', container.into_htsl()


# Whitespace is a real string and is left alone
with Container() as container:
    display_title(' ', ' ')

assert container.into_htsl() == 'title " " " " 1 5 1', container.into_htsl()


# The guard lives at emit time, so direct construction is covered too
with Container() as container:
    DisplayTitleExpression(title='', subtitle='').write()

assert container.into_htsl() == 'title "&r" "&r" 1 5 1', container.into_htsl()


# ...and so is a clone that empties a field
with Container() as container:
    DisplayTitleExpression(title='a', subtitle='b').cloned(subtitle='').write()

assert container.into_htsl() == 'title "a" "&r" 1 5 1', container.into_htsl()


# Same rule for the action bar
with Container() as container:
    display_action_bar('')

assert container.into_htsl() == 'actionBar "&r"', container.into_htsl()
