from unsaid import config


def test_fallback_default(monkeypatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda **kwargs: None)
    monkeypatch.setattr(config, "find_dotenv", lambda **kwargs: "")
    monkeypatch.delenv("UNSAID_FALLBACK_MODELS", raising=False)

    assert config.fallback_models() == ["gemini-3.5-flash-lite"]


def test_fallback_list_from_env(monkeypatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda **kwargs: None)
    monkeypatch.setattr(config, "find_dotenv", lambda **kwargs: "")
    monkeypatch.setenv("UNSAID_FALLBACK_MODELS", " model-a, model-b, ,model-c ")

    assert config.fallback_models() == ["model-a", "model-b", "model-c"]


def test_dotenv_supplies_key_and_model(monkeypatch, tmp_path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "GEMINI_API_KEY=key-from-file\nUNSAID_MODEL=model-from-file\n"
    )
    real_load_dotenv = config.load_dotenv
    monkeypatch.setattr(
        config, "load_dotenv", lambda *args, **kwargs: real_load_dotenv(
            str(dotenv_path), override=False
        )
    )
    monkeypatch.setattr(config, "find_dotenv", lambda **kwargs: str(dotenv_path))
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "UNSAID_MODEL"):
        monkeypatch.delenv(name, raising=False)

    assert config.api_key() == "key-from-file"
    assert config.model_name() == "model-from-file"


def test_shell_variables_win_over_dotenv(monkeypatch, tmp_path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("GEMINI_API_KEY=key-from-file\n")
    real_load_dotenv = config.load_dotenv
    monkeypatch.setattr(
        config, "load_dotenv", lambda *args, **kwargs: real_load_dotenv(
            str(dotenv_path), override=False
        )
    )
    monkeypatch.setattr(config, "find_dotenv", lambda **kwargs: str(dotenv_path))
    monkeypatch.setenv("GEMINI_API_KEY", "key-from-shell")

    assert config.api_key() == "key-from-shell"
