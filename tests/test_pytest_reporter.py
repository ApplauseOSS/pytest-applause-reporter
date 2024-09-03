import responses
from pytest import Pytester
from applause.common_python_reporter import ApplauseConfig
from applause.pytest_applause_reporter import ApplausePytestPlugin

def test_applause_reporter_initialization():
    config = ApplauseConfig(api_key="api_key", product_id=123)
    applause_plugin = ApplausePytestPlugin(config)
    assert applause_plugin.reporter is not None

@responses.activate
def test_pytest_plugin_hooks(pytester: Pytester):
    create_run_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-run/create', json={"runId": 123})
    responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/test-runs/123/heartbeat', json={})
    end_run_call = responses.add(responses.DELETE, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-run/123?endingStatus=COMPLETE', json={})
    provider_info_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result/provider-info', json={})
    create_result_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result/create-result', json={"testResultId": 123})
    submit_result_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result', json={})

    pytester.makeconftest("""
        from applause.common_python_reporter import ApplauseConfig
        from applause.pytest_applause_reporter import ApplausePytestPlugin

        def pytest_configure(config):
            config.pluginmanager.register(ApplausePytestPlugin(ApplauseConfig(api_key="api_key", product_id=123)), 'applause-pytest-plugin')
    """)
    pytester.makepyfile("""
        def test_something(applause_result):
            pass
    """)

    result = pytester.runpytest()
    assert result.ret == 0
    assert create_run_call.call_count == 1
    assert create_result_call.call_count == 1
    assert submit_result_call.call_count == 1
    assert end_run_call.call_count == 1
    assert provider_info_call.call_count == 1

@responses.activate
def test_pytest_plugin_hook_multiple_results(pytester: Pytester):
    create_run_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-run/create', json={"runId": 123})
    responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/test-runs/123/heartbeat', json={})
    end_run_call = responses.add(responses.DELETE, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-run/123?endingStatus=COMPLETE', json={})
    provider_info_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result/provider-info', json={})
    create_result_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result/create-result', json={"testResultId": 123})
    submit_result_call = responses.add(responses.POST, 'https://prod-auto-api.cloud.applause.com:443/api/v1.0/test-result', json={})

    pytester.makeconftest("""
        from applause.common_python_reporter import ApplauseConfig
        from applause.pytest_applause_reporter import ApplausePytestPlugin

        def pytest_configure(config):
            config.pluginmanager.register(ApplausePytestPlugin(ApplauseConfig(api_key="api_key", product_id=123)), 'applause-pytest-plugin')
    """)
    pytester.makepyfile("""
        def test_something(applause_result):
            pass
        def test_something2(applause_result):
            pass
    """)

    result = pytester.runpytest()
    assert result.ret == 0
    assert create_run_call.call_count == 1
    assert create_result_call.call_count == 2
    assert submit_result_call.call_count == 2
    assert end_run_call.call_count == 1
    assert provider_info_call.call_count == 1

