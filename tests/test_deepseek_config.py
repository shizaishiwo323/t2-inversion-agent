from t2_agent.deepseek import get_deepseek_api_key, get_deepseek_api_key_source


class FakeSecrets(dict):
    pass


def test_deepseek_api_key_reads_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")

    value, source = get_deepseek_api_key_source({})

    assert value == "env-key"
    assert source == "environment"
    assert get_deepseek_api_key({}) == "env-key"


def test_deepseek_api_key_prefers_streamlit_secrets(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")

    value, source = get_deepseek_api_key_source(FakeSecrets(DEEPSEEK_API_KEY="secret-key"))

    assert value == "secret-key"
    assert source == "streamlit_secrets"
