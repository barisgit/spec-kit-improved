from specify_cli.services.update_service import UpdateService


def test_check_for_updates_uses_canonical_keys(monkeypatch):
    service = UpdateService()

    # Stub version check to deterministic values
    def fake_check_for_updates(_use_cache=True):
        return True, "1.0.0", "1.1.0"

    monkeypatch.setattr(
        service.version_checker, "check_for_updates", fake_check_for_updates
    )

    # Stub installer and detector
    monkeypatch.setattr(service.installer, "can_auto_update", lambda: True)
    monkeypatch.setattr(service.detector, "detect_installation_method", lambda: "pipx")

    info = service.check_for_updates()

    assert "method" in info
    assert "supports_auto_update" in info
    assert info["method"] == "pipx"
    assert info["supports_auto_update"] is True

    # Old keys should not be present
    assert "installation_method" not in info
    assert "can_auto_update" not in info
