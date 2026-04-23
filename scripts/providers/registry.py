"""Provider レジストリ。プロバイダ名から実装クラスを解決する。

B1時点ではOpenAIのみProvider経由で動作。
Geminiは既存の generate_slide_with_retry.py 内の実装を使う（B3で移植予定）。
"""
from __future__ import annotations

from .base import ImageProvider
from .openai import OpenAIImageProvider


_PROVIDERS: dict[str, type[ImageProvider]] = {
    "openai": OpenAIImageProvider,
}


def get_provider(name: str) -> ImageProvider:
    """プロバイダ名からインスタンスを取得する。

    Raises:
        ValueError: 未知のプロバイダ名
    """
    key = name.lower().strip()
    if key not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(f"Unknown provider: {name!r}. Available: {available}")
    return _PROVIDERS[key]()


def list_providers() -> list[str]:
    """登録済みプロバイダ名の一覧を返す。"""
    return sorted(_PROVIDERS.keys())
