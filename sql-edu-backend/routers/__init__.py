"""FastAPI routers package.

说明（给新手）：
- 本项目的路由注册在 `main.py` 中进行。
- 这里的 `__init__.py` 仅作为可选的导出入口。
"""

from .ai import router as ai_router

__all__ = ["ai_router"]





