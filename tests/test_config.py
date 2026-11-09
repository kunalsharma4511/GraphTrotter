import pytest

from travel_planner import config


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nope")
    with pytest.raises(ValueError):
        config.get_llm()


def test_groq_without_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        config.get_llm()


def test_groq_client_is_built_without_network(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "some-model")
    llm = config.get_llm()
    assert llm.model_name == "some-model"      # ChatGroq stores the name here


def test_ollama_provider_is_selected(monkeypatch):
    pytest.importorskip("langchain_ollama")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", "llama3.1:8b")
    assert config.get_llm().model == "llama3.1:8b"