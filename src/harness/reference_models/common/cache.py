#    Copyright 2018 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Cache engine.
"""
import functools32

# Note: for now only use the lru_cache from functools, backported to Python 2.7 as
# functools32. A better cache engine needs to be implemented that:
# 1) supports sharing across process (optionally)
# 2) ...


# A cache decorator
# Note: for now the cache simply wraps the functools.lrucache.
# Will be expanded for multiprocess support.
def LruCache(maxsize=None):
  """LRU Cache decorator.

  Args:
    maxsize: the maximum cache size, or None for unlimited size.
  """
  def wrapper(fn):
    return functools32.lru_cache(maxsize=maxsize)(fn)

  return wrapper


# Cache management
class CacheManager(object):
  """Cache context manager.

  This uses the `functools.lru_cache` for memoizing calls to
  a function in a LRU fashion. Use it for:
    - temporary speed up through memoizing. The cache is cleared
    when getting out of the 'with' context.
    - get repeatable results of function with random component:
    the function results will be the same within one 'with' context.

  Usage:
    #  Temporarily install a LRU memoizing cache on some function.
    with CacheManager(my_function, maxsize=None) as cm:
      # run the code using my_function
  """
  def __init__(self, fn, maxsize=None):
    self._fn = fn
    self._wrapper_fn = None
    self._maxsize = maxsize

  def __enter__(self):
    self._wrapper_fn = functools32.lru_cache(maxsize=self._maxsize)(self._fn)
    self._overrideModuleFunctionWith(self._wrapper_fn)
    return self

  def __exit__(self, *args):
    self.clear()
    self._overrideModuleFunctionWith(self._fn)

  def clear(self):
    if self._wrapper_fn:
      self._wrapper_fn.cache_clear()

  def cache_info(self):
    if self._wrapper_fn:
      self._wrapper_fn.cache_info()

  def _overrideModuleFunctionWith(self, fn):
    self._fn.func_globals[self._fn.__name__] = fn
