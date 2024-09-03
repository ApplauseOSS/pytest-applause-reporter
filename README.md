# pytest-applause-reporter
A pytest plugin for reporting results to the Applause Automation services.

## Usage

In your conftest.py file, add the following to register the ApplausePyTestPlugin:

```python
def pytest_configure(config: pytest.Config):
    app_config=ApplauseConfig(
        api_key="api_key",
        product_id=123
    )
    config.pluginmanager.register(ApplausePytestPlugin(app_config), 'applause-pytest-plugin')
```

You can then inject the Applause Result into your pytest test case:

```python
def test_something(self, applause_result: ApplauseResult):
    # Some test case
    pass
```

### Registering a Selenium WebDriver

Remote Selenium Webdrivers that are proxied through the Applause Selenium Proxy can be registered to an Applause Result to link up the remote session to the test case result.

```python
def test_something(self, driver: WebDriver, applause_result: ApplauseResult):
    # Some test case
    applause_result.register_session_id(driver.session_id)
    pass
```

### Uploading Assets

You can upload any binary asset to an Applause result

```python
def test_something(self, applause_result: ApplauseResult):
    # Some test case

    asset = "asset".encode("utf-8")
    applause_result.attach_asset(
        asset_name="asset.txt", 
        asset=asset, 
        asset_type=AssetType.UNKNOWN,
    )
    pass
```

## Developing

### Prerequisites

```bash
pip install poetry
poetry install        # installs python dependencies into poetry
poetry install --dev  # installs python dev-dependencies into poetry
```

Optionally, run this command to stick python virtualenv to project directory.

poetry config virtualenvs.in-project true

### Building

We use tox to automate our build pipeline. Running the default tox configuration will install dependencies, format and lint the project, run the unit test and run the build. This will verify the project builds correctly for python 3.8, 3.9, 3.10, and 3.11. 

```bash
poetry run tox
```

### Linting

The plugin can be linted through tox `tox run -e lint`

### Running Unit Tests

The unit tests can be executed through tox `tox run -e test`

### Intellij setup

https://www.jetbrains.com/help/idea/poetry.html

### Helpful commands

```bash
# list details of the poetry environment
poetry env info 

# To activate this project's virtualenv, run the following:
poetry shell

# To exit the virtualenv shell:
exit

# To install packages into this virtualenv:
poetry add YOUR_PACKAGE
```
