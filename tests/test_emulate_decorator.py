from pyhtsw import EmulatedHouse, chat, emulate, function

with EmulatedHouse():

    @function('emulate decorator test')
    def func() -> None:
        chat('hello from the test function')

    # The block's callback has not run yet -- nothing has finalized.
    assert func.block is not None
    assert func.block.is_empty(), func.block


# Exiting the context above finalized the block, running its callback. The
# `emulate` callback runs even later (atexit), so it sees the populated block.
@emulate()
def run() -> None:
    assert func.block is not None
    assert not func.block.is_empty(), func.block
