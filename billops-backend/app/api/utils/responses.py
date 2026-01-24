from typing import Any


def ok(data: Any) -> dict[str, Any]:
    return {"data": data}


def error(message: str) -> dict[str, str]:
    return {"error": message}
