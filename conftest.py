import os
import pytest
import logging
from dotenv import load_dotenv
from test.src.constants import constants

logger = logging.getLogger(__name__)
load_dotenv() 

ENVIRONMENTS = {
    "LOCAL": "data.envtest.data_local",
    "QA": "data.envtest.data_qa",
    "STG": "data.envtest.data_stg",
    "DEV": "data.envtest.data_dev",
    "PROD": "data.envtest.data_prod"
}

def pytest_addoption(parser):
    parser.addoption(
        "--envtest",
        action="store",
        dest="envtest",
        help="Test environment",
        choices=("LOCAL", "QA", "STG", "DEV", "PROD")
    )
    parser.addoption(
        "--module",
        action="store",
        dest="module",
        default="All",
        help="Module to be tested"
    )
    parser.addoption(
        "--stg",
        action="store_true",
        dest="stg",
        default=False,
        help="Run tests on staging environment"
    )
    parser.addoption(
        "--dev",
        action="store_true",
        dest="dev",
        default=False,
        help="Run tests on dev environment"
    )
    parser.addoption(
        "--prod",
        action="store_true",
        dest="prod",
        default=False,
        help="Run tests on production environment"
    )

def env_manage(config, env_name):
    if env_name:
        constants.ENV = env_name
    logger.warning(f"Running tests on {env_name} environment")
    os.environ['SIMPLE_SETTINGS'] = ENVIRONMENTS[constants.ENV]
    if not config.getoption('r'):
        config.option.allure_report_dir = 'allure/allure-results'

def env_setup(config):
    if config.getoption('stg'):
        env_manage(config, "STG")
    elif config.getoption('dev'):
        env_manage(config, "DEV")
    elif config.getoption('prod'):
        env_manage(config, "PROD")
    else:
        env_manage(config, config.getoption('envtest'))

def pytest_configure(config):
    constants.MODULE = config.getoption('module')

    env_setup(config)

    config.option.maxfail = 5
