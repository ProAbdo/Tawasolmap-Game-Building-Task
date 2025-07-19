from functools import wraps
from asgiref.sync import sync_to_async

def require_auth(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.player:
            return await self.send_error("Not authenticated")

        await sync_to_async(self.player.refresh_from_db)()
        return await func(self, *args, **kwargs)

    return wrapper