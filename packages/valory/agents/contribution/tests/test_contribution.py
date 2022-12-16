# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Integration tests for the valory/oracle_abci skill."""

# pylint: skip-file

from pathlib import Path
from typing import Tuple
import json
import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.fixture_helpers import abci_host  # noqa: F401
from aea_test_autonomy.fixture_helpers import abci_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import flask_tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_configuration  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_class  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_function  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import key_pairs  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint_port  # noqa: F401
from packages.valory.agents.contribution.tests.helpers.fixtures import (  # noqa: F401
    UseHardHatContributionBaseTest,
    UseMockGoogleSheetsApiBaseTest,
)
from packages.valory.agents.contribution.tests.helpers.docker import (
    DEFAULT_JSON_SERVER_ADDR as _DEFAULT_JSON_SERVER_ADDR,
)
from packages.valory.agents.contribution.tests.helpers.docker import (
    DEFAULT_JSON_SERVER_PORT as _DEFAULT_JSON_SERVER_PORT,
)
from packages.valory.skills.abstract_round_abci.tests.test_io.test_ipfs import (  # noqa: F401
    ipfs_daemon,
)


HAPPY_PATH: Tuple[RoundChecks, ...] = (
    RoundChecks("registration_startup"),
    RoundChecks("new_tokens", n_periods=2),
    RoundChecks("leaderboard_observation", n_periods=2),
    RoundChecks("image_code_calculation", n_periods=2),
    RoundChecks("image_generation", n_periods=2),
    RoundChecks("db_update", n_periods=2),
    RoundChecks("reset_and_pause", n_periods=2),
)

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Got the new token list:",
    "Calculated token updates:",
    "Generated the following new images:",
    "Updating database tables",
    "Period end",
)
PACKAGES_DIR = Path(__file__).parent.parent.parent.parent.parent


MOCK_API_ADDRESS = _DEFAULT_JSON_SERVER_ADDR
MOCK_API_PORT = _DEFAULT_JSON_SERVER_PORT
MOCK_WHITELIST_ADDRESS = _DEFAULT_JSON_SERVER_ADDR
MOCK_IPFS_ADDRESS = _DEFAULT_JSON_SERVER_ADDR

# This variable contains a dummy RSA key
DUMMY_SERVICE_AUTH = {
    "type": "service_account",
    "project_id": "my_dummy_project_id",
    "private_key_id": "my_private_key_id",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA7kaACkWf+PD2BNPg6SoUcnET2P3FWQsO3g0+clqRfyGQK3P1\n1xPk20fGJgbyvq6Y/DduR50QxIwXuF0iS6QEX5+CB9rwhrevvBwrT2k1QjccEJMB\njnkTREzhpfTH0T5udzfc23wGE8oCYPOtPa0NL9FmxI6DmedOzZiNrlMpMTSzqjm/\ndam+ZzbQwFg6NnywRwdKkeQY9jyHyN21fqXkSd0dtslO7zKcMvxGXAwHvmG34pjW\na6t7WxAjkIvm6uqM4DJHYk9eXKXooRawYTARAiLRkw9UL5Ug1bd6kFml3F8R2ac+\nSe08zczxZbGwXdnayjDGYTbt9TcxFLl32X9DpQIDAQABAoIBAQC90mhaxpDlD4HO\n4sTAvAdCDJeVPMYlY8vaVo6zJzfWIfTqyRzG1VBy6MEQtmRYSFwUQkyWvKgJDNow\nw/F4dRgO3dIHVAJeMKPNpltSjiwhrimrgpGw4P/aX608Or+dELGMRHKsYCevSDWQ\n60/OXLiuqZHHcQmiaEW9QJVOlW2xhhMJMRXHfhpkbHDNH6LUJyqFMjNcIzl/cRcF\n05FkDl9ha1v7oeqsBuaykiGnWJpjEeUMwmr14lR4qk6I/xACmubD6eRpi5dJfLGD\nq7zHo+FS1dGu4GqXb5IiGeXKNhlu2bPwwqTHP1ILnnGyyglhh7vp+zUSRjIqVSAi\nU2XkzgdZAoGBAP83tt4WXEW0ZbDTRQl5lVJY+DKIv6wW8idPKM7Dl1p6TBNH1ecU\nCY0AMPpM/7UNkuj/Urq4OnDvvzQLvuM0ixhLl28uPwufgkWsDIdNFYgMOTvnrPKs\nwhpCvYCIVE2NVsgvaS6S6/x/97JcKu1OYi0sebo66/aEqQyg0idN9C5vAoGBAO8B\nfXtkIMYW1vGco7WyNvQdjvBs5sX2IwzhQEkfJMNCM5ZWrhnu+0TfTA5Wwx5Qwtf0\npNS/wxciJ80SXsOq3YWNN6FMnAr4HatUh50LRkb9CUReqEjbq74lAXMmyNmff9Xl\nex6F9jtqb7FlKP2qnwteO1KmwyJFp7IrfopVh3krAoGBAOEHhfTSMG/BfPxpe/C7\nxF6EVetwydf5r2/bizasHLLJLHS/nSoPb9BkP8siw0AnhMZuAcrjD5xut98zEA+T\nT6WPWSnN1AbykNHPvog5/mcjp/9a6hJbIxY2jJJdIj/zBHaj3xESuIK9bnBUdgEh\nYM1F7tq2g0GsfMXGsyW2xTt/AoGAOmtf05BG3oRop4gFD/1upz6uWKAVzF98c8J/\nJyBgqQV+fInVZmteqZf3DC4y5S8SYRzgSUxSEE598gdCeItEOEerSFbkcV3ySpWP\nzFgcJm/lGvwUIDLpiMGc2Burzl3JLmw4Kt7Nr/o1MOQsH8zbsTioQWyXl8H02nz9\nIi0Dvx8CgYApRW/0hTjwNXmwWZGfEhYbJFG2rAoK0PussZiDIuhWOQHU7wwHqbio\n7FjKzLdY5WkRMCULAOlumFOxk71UCECApDbQ77iML5a+u2Mgn+Wv35Vn+Vqp51Vx\n2iZgR4dnj1Szm8qhe+oiJcnQ3/SGAcEx3mYamgWezlQ5ih1uqc1bPg==\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "my_dummy_project_id@appspot.gserviceaccount.com",
    "client_id": "",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/my_dummy_project_id%40appspot.gserviceaccount.com",
}


@pytest.mark.usefixtures("ipfs_daemon")
class BaseTestEnd2EndContributionNormalExecution(BaseTestEnd2EndExecution):
    """Base class for the contribution service e2e tests."""

    agent_package = "valory/contribution:0.1.0"
    skill_package = "valory/contribution_skill_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR

    __param_args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    __sheet_args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.sheet.args"

    extra_configs = [
        {
            "dotted_path": f"{__param_args_prefix}.leaderboard_base_endpoint",
            "value": f"{MOCK_API_ADDRESS}:{MOCK_API_PORT}",
        },
        {
            "dotted_path": f"{__param_args_prefix}.leaderboard_sheet_id",
            "value": "mock_sheet_id",
        },
        {
            "dotted_path": f"{__param_args_prefix}.ipfs_domain_name",
            "value": "/dns/localhost/tcp/5001/http",
        },
        {
            "dotted_path": f"{__param_args_prefix}.whitelist_endpoint",
            "value": f"{MOCK_WHITELIST_ADDRESS}:{MOCK_API_PORT}/mock_whitelist",
        },
        {
            "dotted_path": f"{__param_args_prefix}.ipfs_gateway_base_url",
            "value": f"{MOCK_IPFS_ADDRESS}:{MOCK_API_PORT}/mock_ipfs/",
        },
        {
            "dotted_path": f"{__sheet_args_prefix}.service_auth",
            "value": json.dumps(DUMMY_SERVICE_AUTH),
        },
    ]

    http_server_port_config = {
        "dotted_path": "vendor.fetchai.connections.http_server.config.port",
        "value": 8000,
    }

    def _BaseTestEnd2End__set_extra_configs(self) -> None:
        """Set the current agent's extra config overrides that are skill specific."""
        for config in self.extra_configs:
            self.set_config(**config)

        self.set_config(**self.http_server_port_config)
        self.http_server_port_config["value"] += 1  # port number increment


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestEnd2EndContributionSingleAgent(
    BaseTestEnd2EndContributionNormalExecution,
    UseMockGoogleSheetsApiBaseTest,
    UseHardHatContributionBaseTest,
):
    """Test the contribution skill with only one agent."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (2,))
class TestEnd2EndContributionTwoAgents(
    BaseTestEnd2EndContributionNormalExecution,
    UseMockGoogleSheetsApiBaseTest,
    UseHardHatContributionBaseTest,
):
    """Test the contribution skill with two agents."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (4,))
class TestEnd2EndContributionFourAgents(
    BaseTestEnd2EndContributionNormalExecution,
    UseMockGoogleSheetsApiBaseTest,
    UseHardHatContributionBaseTest,
):
    """Test the contribution skill with four agents."""
