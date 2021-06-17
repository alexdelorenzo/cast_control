# just import newer `typing` features here so this pattern
# isn't repeated throughout the project.

# Protocol, Final, etc are not available on Python 3.7
try:
  # Python 3.8 - 3.9+
  from typing import Protocol, runtime_checkable, Final

except ImportError:
  # Python 3.7
  from typing_extensions import \
    Protocol, runtime_checkable, Final
