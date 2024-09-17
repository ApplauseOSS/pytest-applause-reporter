"""PyTest Plugin for reporting test results to the Applause Services.

This module provides a PyTest plugin for reporting test results to the Applause Services. It includes a fixture for generating an ApplauseReporter object for use within a
PyTest session, and a fixture for generating an ApplauseResult object for use within a PyTest function.

Example:
-------
def pytest_configure(config: pytest.Config):
    app_config=ApplauseConfig(
        api_key="api_key",
        product_id=123
    )
    config.pluginmanager.register(ApplausePytestPlugin(app_config), 'applause-pytest-plugin')

def test_something(applause_result: ApplauseResult):
    # Test case

"""

from typing import Generator, Optional, List
import pytest
from _pytest.nodes import Node
from _pytest.reports import ExceptionChainRepr
import sys
from applause.common_python_reporter import ApplauseConfig, ApplauseReporter
from applause.common_python_reporter.dtos import TestResultStatus, AssetType
from applause.common_python_reporter.email_helper import EmailHelper


class ApplauseResult:
    """A class for tracking the result of a test case, and performing actions on it.

    Attributes
    ----------
        reporter (ApplauseReporter): The ApplauseReporter object.
        nodeid (str): The pytest node ID.
        provider_session_guids (List[str]): The list of provider session GUIDs.

    """

    def __init__(self, reporter: ApplauseReporter, nodeid: str):
        """Initialize an instance of the class.

        Args:
        ----
            reporter (ApplauseReporter): The ApplauseReporter object.
            nodeid (str): The node ID.

        Attributes:
        ----------
            reporter (ApplauseReporter): The ApplauseReporter object.
            nodeid (str): The node ID.
            applause_test_case_id (None): The Applause test case ID.
            testrail_test_case_id (None): The TestRail test case ID.
            provider_session_guids (List[str]): The list of provider session GUIDs.

        Returns:
        -------
            None

        """
        self.reporter = reporter
        self.nodeid = nodeid
        self.provider_session_guids: List[str] = []
        self.result_logs = []

    def register_session_id(self, provider_session_guid: str):
        """Register a provider session ID to the Applause Test Case Result.

        Args:
        ----
            provider_session_guid (str): The provider session GUID to be registered.

        Returns:
        -------
            None

        """
        self.provider_session_guids.append(provider_session_guid)

    def log(self, message: str):
        """Print a message to the console and store it in the result logs. Result logs are attached as an asset to the test case after the result is completed.

        Args:
        ----
            message (str): The message to be logged.

        """
        sys.stdout.write(message)
        self.result_logs.append(message)

    def attach_asset(self, asset_name: str, asset: bytes, asset_type: AssetType, provider_session_guid: Optional[str] = None) -> None:
        """Attach an asset to the test case.

        Args:
        ----
            asset_name (str): The name of the asset.
            asset (bytes): The asset data.
            asset_type (AssetType): The type of the asset.
            provider_session_guid (Optional[str]): The provider session GUID (default: None).

        Returns:
        -------
        None

        """
        if provider_session_guid is not None:
            self.provider_session_guids.append(provider_session_guid)
        self.reporter.attach_test_case_asset(id=self.nodeid, asset_name=asset_name, asset=asset, assetType=asset_type, provider_session_guid=provider_session_guid)


class ApplausePytestPlugin:
    """A PyTest plugin for reporting test results to the Applause Services.

    Attributes
    ----------
        reporter (ApplauseReporter): The underlying ApplauseReporter object.
        auto_api (AutoApi): The AutoAPI object for interacting with the Applause Services.

    """

    def __init__(self, config: ApplauseConfig):
        """Initialize an instance of the ApplauseReporter class.

        Args:
        ----
            config (ApplauseConfig): The configuration object for the reporter.

        """
        self.reporter = ApplauseReporter(config=config)
        self.auto_api = self.reporter.auto_api
        pass

    # set up a hook to be able to check if a test has failed
    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item):
        """Mark the pytest item with a status once it is known by pytest.

        Args:
        ----
            item (pytest.Item): The pytest item object.

        """
        outcome = yield
        rep: pytest.TestReport = outcome.get_result()
        item.status = rep

    @pytest.fixture(scope="session")
    def applause_reporter(self, request: pytest.FixtureRequest) -> Generator[ApplauseReporter, None, None]:
        """Generate an Applause Reporter for use within a PyTest session.

        Args:
        ----
            request (pytest.FixtureRequest): The pytest fixture request object.

        Yields:
        ------
            ApplauseReporter: An instance of ApplauseReporter for reporting test results.

        """
        self.reporter.runner_start(tests=[item.name for item in request.session.items])
        yield self.reporter
        self.reporter.runner_end()

    @pytest.fixture(scope="session")
    def email_helper(self) -> Generator[EmailHelper, None, None]:
        """Generate an EmailHelper for use within a PyTest session.

        Args:
        ----
            request (pytest.FixtureRequest): The pytest fixture request object.

        Yields:
        ------
            EmailHelper: An instance of EmailHelper for email testing.

        """
        yield EmailHelper(auto_api=self.auto_api)

    @pytest.fixture(scope="function")
    def applause_result(self, request: pytest.FixtureRequest, applause_reporter: ApplauseReporter) -> Generator[ApplauseResult, None, None]:
        """Generate an ApplauseResult for use within a PyTest function.

        Args:
        ----
            request (pytest.FixtureRequest): The pytest fixture request object.
            applause_reporter (ApplauseReporter): The ApplauseReporter object used for reporting.

        Yields:
        ------
            ApplauseResult: The result tracker object used for tracking the test case result.

        """
        node: Node = request.node
        applause_test_case_id = node.get_closest_marker("applause_test_case_id")
        test_rail_test_case_id = node.get_closest_marker("test_rail_test_case_id")
        applause_reporter.start_test_case(id=node.nodeid, test_case_name=node.name, provider_session_ids=[])
        result_tracker = ApplauseResult(reporter=self.reporter, nodeid=node.nodeid)
        result_tracker.log(f"Starting test case {node.name}")

        # Yield the result tracker to the test
        yield result_tracker

        status: pytest.TestReport = node.status
        result_status = TestResultStatus.FAILED if status.failed else TestResultStatus.PASSED
        error_rep: ExceptionChainRepr = status.longrepr

        # Add some log messages to the result tracker
        result_tracker.log(f"Test case {node.name} has completed with status: {'FAILED' if status.failed else 'PASSED'}")
        if status.failed:
            result_tracker.log(status.longreprtext)

        result_tracker.attach_asset(asset_name="console_log.txt", asset="\n".join(result_tracker.result_logs), asset_type=AssetType.CONSOLE_LOG)

        applause_reporter.submit_test_case_result(
            id=node.nodeid,
            status=result_status,
            failure_reason=error_rep.reprcrash.message if status.failed else None,
            provider_session_guids=list(result_tracker.provider_session_guids),
            applause_test_case_id=applause_test_case_id.args[0] if applause_test_case_id is not None else None,
            test_rail_case_id=test_rail_test_case_id.args[0] if test_rail_test_case_id is not None else None,
        )
