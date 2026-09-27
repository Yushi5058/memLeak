"""Entry point for memLeak.

The PyWeek packaging convention is that judges should be able to see how to
run the game from this one file. This module also fails fast with a clear
message on an interpreter that is too old, because the judge cannot guess
which version to use.
"""

import sys

MIN_VER = (3, 10)

if sys.version_info[:2] < MIN_VER:
    running = sys.version.split()[0]
    sys.exit(
        f"memLeak needs Python {MIN_VER[0]}.{MIN_VER[1]} or newer. "
        f"You are on Python {running}."
    )

import main  # noqa: E402  # the version guard has to run before this import

if __name__ == "__main__":
    main.main()
