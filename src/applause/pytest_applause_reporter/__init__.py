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
from applause.common_python_reporter import ApplauseConfig, ApplauseReporter
from applause.common_python_reporter.dtos import TestResultStatus, AssetType


class ApplauseResult:
    """A class for tracking the result of a test case, and performing actions on it.

    Attributes
    ----------
        reporter (ApplauseReporter): The ApplauseReporter object.
        nodeid (str): The pytest node ID.
        applause_test_case_id (None): The Applause test case ID.
        testrail_test_case_id (None): The TestRail test case ID.
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
        self.applause_test_case_id: Optional[str] = None
        self.testrail_test_case_id: Optional[str] = None
        self.provider_session_guids: List[str] = []

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

    """

    def __init__(self, config: ApplauseConfig):
        """Initialize an instance of the ApplauseReporter class.

        Args:
        ----
            config (ApplauseConfig): The configuration object for the reporter.

        """
        self.reporter = ApplauseReporter(config=config)
        pass

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
        applause_reporter.start_test_case(id=request.node.nodeid, test_case_name=request.node.name, provider_session_ids=[])
        result_tracker = ApplauseResult(reporter=self.reporter, nodeid=request.node.nodeid)
        yield result_tracker

        applause_reporter.submit_test_case_result(
            id=request.node.nodeid,
            status=TestResultStatus.PASSED,
            provider_session_guids=list(result_tracker.provider_session_guids),
            applause_test_case_id=result_tracker.applause_test_case_id,
            test_rail_case_id=result_tracker.testrail_test_case_id,
        )
