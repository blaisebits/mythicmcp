"""Live Mythic smoke test for runtime reload behavior.

Run with:
    uv run --env-file .env python scripts/dev_hotload_smoke.py
"""

from __future__ import annotations

import asyncio
import json

from mythicmcp.config import load_config
from mythicmcp.connection import MythicContext, connect_to_mythic
from mythicmcp.server import reload_runtime
from mythicmcp.tools.callbacks import list_callbacks
from mythicmcp.tools.status import check_connection


async def main() -> None:
    config = load_config()
    mythic_instance = await connect_to_mythic(config)
    mythic_ctx = MythicContext(mythic=mythic_instance, config=config)

    before = await check_connection(mythic_ctx)
    callbacks_before = await list_callbacks(mythic_instance)
    reload_result = reload_runtime()
    after = await check_connection(mythic_ctx)
    callbacks_after = await list_callbacks(mythic_instance)

    print(json.dumps({
        "before": before.model_dump(mode="json"),
        "callbacks_before": callbacks_before.count,
        "reload": reload_result.model_dump(mode="json"),
        "after": after.model_dump(mode="json"),
        "callbacks_after": callbacks_after.count,
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
