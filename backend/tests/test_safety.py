from app.agent.safety import is_auto_executable, requires_approval, risk_for_action


def test_low_risk_actions_are_auto_executable():
    for action in ["retry_service", "rerun_health_check", "gather_logs"]:
        risk = risk_for_action(action)
        assert risk == "low"
        assert is_auto_executable(risk)
        assert not requires_approval(risk)


def test_medium_risk_actions_require_approval():
    for action in ["restore_env_var", "rollback_revision", "fix_dependency_config"]:
        risk = risk_for_action(action)
        assert risk == "medium"
        assert not is_auto_executable(risk)
        assert requires_approval(risk)


def test_unknown_action_is_not_whitelisted():
    assert risk_for_action("delete_data") is None
    assert risk_for_action("rotate_credentials") is None
    assert risk_for_action("something_made_up") is None
