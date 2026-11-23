from __future__ import annotations

from app.bot.dispatcher import build_dispatcher
from app.bot.handlers import analytics, common, content, ideas, leads, menu, review, tasks
from app.config import Settings


def test_build_dispatcher_registers_all_routers() -> None:
    dp = build_dispatcher(Settings(_env_file=None))
    assert dp is not None
    routers = (
        common.router,
        content.router,
        ideas.router,
        tasks.router,
        analytics.router,
        leads.router,
        review.router,
        menu.router,
    )
    for router in routers:
        assert len(router.message.handlers) > 0, f"{router.name} has no message handlers"
        assert len(router.callback_query.handlers) > 0, f"{router.name} has no callback handlers"
