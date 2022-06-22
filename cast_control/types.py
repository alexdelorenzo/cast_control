# just import newer `typing` features here so this pattern
# isn't repeated throughout the project.

try:
    from typing import Protocol, runtime_checkable, Final

except ImportError:
    from typing_extensions import Protocol, runtime_checkable, Final
