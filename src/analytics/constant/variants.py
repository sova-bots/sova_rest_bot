from ..api import get_departments


async def all_departments(tgid: int) -> dict:
    return await get_departments(tgid)
