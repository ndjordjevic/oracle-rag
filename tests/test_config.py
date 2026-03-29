"""Tests for configuration (env vars)."""

from __future__ import annotations

import os

import pytest
from youtube_transcript_api.proxies import GenericProxyConfig

from pinrag.config import (
    DEFAULT_LLM_MODEL_OPENROUTER,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_MAX_INDEX_FILE_BYTES,
    DEFAULT_OPENROUTER_APP_TITLE,
    DEFAULT_OPENROUTER_APP_URL,
    get_chunk_overlap,
    get_chunk_size,
    get_collection_name,
    get_llm_model,
    get_llm_model_fallbacks,
    get_llm_provider,
    get_openrouter_app_title,
    get_openrouter_app_url,
    get_openrouter_sort,
    sync_openrouter_sdk_attribution_env,
    get_persist_dir,
    get_plaintext_max_file_bytes,
    get_rerank_retrieve_k,
    get_rerank_top_n,
    get_use_rerank,
    get_yt_proxy_config,
    get_yt_vision_image_detail,
)


def test_get_llm_provider_default_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset PINRAG_LLM_PROVIDER defaults to openrouter."""
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    assert get_llm_provider() == DEFAULT_LLM_PROVIDER == "openrouter"


def test_get_llm_model_default_openrouter_free(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset model env with default provider uses openrouter/free."""
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("PINRAG_LLM_MODEL", raising=False)
    assert get_llm_model() == DEFAULT_LLM_MODEL_OPENROUTER == "openrouter/free"


def test_openrouter_app_attribution_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_APP_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_APP_TITLE", raising=False)
    assert get_openrouter_app_url() == DEFAULT_OPENROUTER_APP_URL
    assert get_openrouter_app_title() == DEFAULT_OPENROUTER_APP_TITLE


def test_openrouter_app_attribution_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_APP_URL", "https://example.com/app")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "Custom")
    assert get_openrouter_app_url() == "https://example.com/app"
    assert get_openrouter_app_title() == "Custom"


def test_sync_openrouter_sdk_attribution_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_APP_URL", "https://a.example")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "T")
    sync_openrouter_sdk_attribution_env()
    assert os.environ.get("OPENROUTER_HTTP_REFERER") == "https://a.example"
    assert os.environ.get("OPENROUTER_X_OPEN_ROUTER_TITLE") == "T"


def test_get_llm_model_fallbacks_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PINRAG_LLM_MODEL_FALLBACKS", raising=False)
    assert get_llm_model_fallbacks() is None


def test_get_llm_model_fallbacks_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PINRAG_LLM_MODEL_FALLBACKS",
        "a/b:free, c/d ,",
    )
    assert get_llm_model_fallbacks() == ["a/b:free", "c/d"]


def test_get_openrouter_sort_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PINRAG_OPENROUTER_SORT", raising=False)
    assert get_openrouter_sort() is None


def test_get_openrouter_sort_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_OPENROUTER_SORT", "Latency")
    assert get_openrouter_sort() == "latency"


def test_get_openrouter_sort_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_OPENROUTER_SORT", "cheapest")
    assert get_openrouter_sort() is None


def test_get_chunk_size_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns default 1000."""
    monkeypatch.delenv("PINRAG_CHUNK_SIZE", raising=False)
    assert get_chunk_size() == 1000


def test_get_chunk_size_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("PINRAG_CHUNK_SIZE", "1500")
    assert get_chunk_size() == 1500


def test_get_chunk_size_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With invalid env var, returns default."""
    monkeypatch.setenv("PINRAG_CHUNK_SIZE", "not_a_number")
    assert get_chunk_size() == 1000


def test_get_chunk_size_negative_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With negative value, returns default."""
    monkeypatch.setenv("PINRAG_CHUNK_SIZE", "-1")
    assert get_chunk_size() == 1000


def test_get_chunk_overlap_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns default 200."""
    monkeypatch.delenv("PINRAG_CHUNK_OVERLAP", raising=False)
    assert get_chunk_overlap() == 200


def test_get_chunk_overlap_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("PINRAG_CHUNK_OVERLAP", "300")
    assert get_chunk_overlap() == 300


def test_get_chunk_overlap_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero overlap is valid."""
    monkeypatch.setenv("PINRAG_CHUNK_OVERLAP", "0")
    assert get_chunk_overlap() == 0


def test_get_chunk_overlap_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With invalid env var, returns default."""
    monkeypatch.setenv("PINRAG_CHUNK_OVERLAP", "abc")
    assert get_chunk_overlap() == 200


def test_get_chunk_overlap_clamped_below_chunk_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When overlap >= chunk size, returns chunk_size - 1."""
    monkeypatch.setenv("PINRAG_CHUNK_SIZE", "500")
    monkeypatch.setenv("PINRAG_CHUNK_OVERLAP", "600")
    assert get_chunk_overlap() == 499


def test_get_chunk_overlap_clamped_chunk_size_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chunk size 1 forces overlap 0 when user asks for more."""
    monkeypatch.setenv("PINRAG_CHUNK_SIZE", "1")
    monkeypatch.setenv("PINRAG_CHUNK_OVERLAP", "5")
    assert get_chunk_overlap() == 0


def test_get_persist_dir_default_and_strip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset uses default; blank/whitespace falls back; values are stripped."""
    monkeypatch.delenv("PINRAG_PERSIST_DIR", raising=False)
    assert get_persist_dir() == "chroma_db"
    monkeypatch.setenv("PINRAG_PERSIST_DIR", "   ")
    assert get_persist_dir() == "chroma_db"
    monkeypatch.setenv("PINRAG_PERSIST_DIR", "  /tmp/pin  ")
    assert get_persist_dir() == "/tmp/pin"


def test_get_collection_name_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With PINRAG_COLLECTION_NAME set, returns that value."""
    monkeypatch.setenv("PINRAG_COLLECTION_NAME", "my_custom_collection")
    assert get_collection_name() == "my_custom_collection"


def test_get_collection_name_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without PINRAG_COLLECTION_NAME, returns pinrag."""
    monkeypatch.delenv("PINRAG_COLLECTION_NAME", raising=False)
    assert get_collection_name() == "pinrag"


# Plaintext max file bytes
def test_get_plaintext_max_file_bytes_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns default 524288 (512 KB)."""
    monkeypatch.delenv("PINRAG_PLAINTEXT_MAX_FILE_BYTES", raising=False)
    assert get_plaintext_max_file_bytes() == DEFAULT_MAX_INDEX_FILE_BYTES


def test_get_plaintext_max_file_bytes_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("PINRAG_PLAINTEXT_MAX_FILE_BYTES", "262144")
    assert get_plaintext_max_file_bytes() == 262144


def test_get_plaintext_max_file_bytes_invalid_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With invalid env var, returns default."""
    monkeypatch.setenv("PINRAG_PLAINTEXT_MAX_FILE_BYTES", "not_a_number")
    assert get_plaintext_max_file_bytes() == DEFAULT_MAX_INDEX_FILE_BYTES


def test_get_plaintext_max_file_bytes_negative_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With negative value, returns default."""
    monkeypatch.setenv("PINRAG_PLAINTEXT_MAX_FILE_BYTES", "-1")
    assert get_plaintext_max_file_bytes() == DEFAULT_MAX_INDEX_FILE_BYTES


# Re-ranking config
def test_get_use_rerank_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns False."""
    monkeypatch.delenv("PINRAG_USE_RERANK", raising=False)
    assert get_use_rerank() is False


def test_get_use_rerank_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """With 1, true, yes, on (case-insensitive), returns True."""
    for val in ("1", "true", "True", "yes", "YES", "on", "ON"):
        monkeypatch.setenv("PINRAG_USE_RERANK", val)
        assert get_use_rerank() is True


def test_get_use_rerank_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """With 0, false, no, off, returns False."""
    for val in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("PINRAG_USE_RERANK", val)
        assert get_use_rerank() is False


def test_get_rerank_retrieve_k_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, falls back to get_retrieve_k() (default 20)."""
    monkeypatch.delenv("PINRAG_RETRIEVE_K", raising=False)
    monkeypatch.delenv("PINRAG_RERANK_RETRIEVE_K", raising=False)
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_retrieve_k_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("PINRAG_RERANK_RETRIEVE_K", "20")
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_retrieve_k_invalid_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With invalid env var, falls back to get_retrieve_k() (default 20)."""
    monkeypatch.delenv("PINRAG_RETRIEVE_K", raising=False)
    monkeypatch.setenv("PINRAG_RERANK_RETRIEVE_K", "x")
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_top_n_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns 10."""
    monkeypatch.delenv("PINRAG_RERANK_TOP_N", raising=False)
    assert get_rerank_top_n() == 10


def test_get_rerank_top_n_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("PINRAG_RERANK_TOP_N", "3")
    assert get_rerank_top_n() == 3


def test_get_rerank_top_n_capped_by_rerank_retrieve_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """top_n cannot exceed rerank retrieve pool size."""
    monkeypatch.delenv("PINRAG_RETRIEVE_K", raising=False)
    monkeypatch.setenv("PINRAG_RERANK_RETRIEVE_K", "15")
    monkeypatch.setenv("PINRAG_RERANK_TOP_N", "100")
    assert get_rerank_top_n() == 15


def test_get_rerank_top_n_default_respects_small_retrieve_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default top_n is capped when retrieve k is below default top_n."""
    monkeypatch.delenv("PINRAG_RERANK_TOP_N", raising=False)
    monkeypatch.delenv("PINRAG_RERANK_RETRIEVE_K", raising=False)
    monkeypatch.setenv("PINRAG_RETRIEVE_K", "5")
    assert get_rerank_retrieve_k() == 5
    assert get_rerank_top_n() == 5


# YouTube transcript proxy config
def _clear_yt_proxy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all YouTube proxy env vars."""
    for key in (
        "PINRAG_YT_PROXY_HTTP_URL",
        "PINRAG_YT_PROXY_HTTPS_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_get_yt_proxy_config_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without any proxy env vars, returns None."""
    _clear_yt_proxy_env(monkeypatch)
    assert get_yt_proxy_config() is None


def test_get_yt_proxy_config_generic_when_http_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With PINRAG_YT_PROXY_HTTP_URL, returns GenericProxyConfig."""
    _clear_yt_proxy_env(monkeypatch)
    monkeypatch.setenv("PINRAG_YT_PROXY_HTTP_URL", "http://proxy.example.com:8080")
    cfg = get_yt_proxy_config()
    assert isinstance(cfg, GenericProxyConfig)


def test_get_yt_proxy_config_generic_when_https_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With PINRAG_YT_PROXY_HTTPS_URL, returns GenericProxyConfig."""
    _clear_yt_proxy_env(monkeypatch)
    monkeypatch.setenv("PINRAG_YT_PROXY_HTTPS_URL", "https://proxy.example.com:8443")
    cfg = get_yt_proxy_config()
    assert isinstance(cfg, GenericProxyConfig)


def test_get_yt_vision_image_detail_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PINRAG_YT_VISION_IMAGE_DETAIL", raising=False)
    assert get_yt_vision_image_detail() == "low"


def test_get_yt_vision_image_detail_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_YT_VISION_IMAGE_DETAIL", "HIGH")
    assert get_yt_vision_image_detail() == "high"


def test_get_yt_vision_image_detail_invalid_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PINRAG_YT_VISION_IMAGE_DETAIL", "ultra")
    assert get_yt_vision_image_detail() == "low"
