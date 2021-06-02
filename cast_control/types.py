# Just import Protocol here so this pattern doesn't
# need to be used more than once
try:
  # Python 3.8+
  from typing import Protocol, runtime_checkable

except ImportError:
  # Python 3.7
  from typing_extensions import Protocol, runtime_checkable
