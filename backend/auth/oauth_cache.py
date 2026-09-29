import time


class OAuthStateCache:
    def __init__(self):
        self._data = {}

    async def set(self, key, value, expires=None):
        expiry = time.time() + (expires or 600)
        self._data[key] = (value, expiry)

    async def get(self, key):
        item = self._data.get(key)
        if item is None:
            return None

        value, expiry = item

        if time.time() >= expiry:
            self._data.pop(key, None)
            return None

        return value

    async def delete(self, key):
        self._data.pop(key, None)


oauth_state_cache = OAuthStateCache()
