# Just import Protocol here so this pattern doesn't
# need to be used more than once
try:
  from typing import Protocol  # Python 3.8+

except ImportError:
  from typing_extensions import Protocol  # Python 3.7
