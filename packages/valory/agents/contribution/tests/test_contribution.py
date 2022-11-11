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

from copy import deepcopy
from pathlib import Path
from typing import Tuple

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
    UseHardHatAutoFundBaseTest,
)


HAPPY_PATH: Tuple[RoundChecks, ...] = (
    RoundChecks("registration_startup"),
    RoundChecks("new_members", n_periods=2),
    RoundChecks("leaderboard_observation", n_periods=2),
    RoundChecks("image_code_calculation", n_periods=2),
    RoundChecks("image_generation", n_periods=2),
    RoundChecks("db_update", n_periods=2),
    RoundChecks("reset_and_pause", n_periods=2),
)

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Got the new member list:",
    "Calculated member updates:",
    "Generated the following new images:",
    "Updating database tables",
    "Period end",
)
PACKAGES_DIR = Path(__file__).parent.parent.parent.parent.parent


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIPriceEstimationSingleAgent(
    BaseTestEnd2EndExecution,
    UseHardHatAutoFundBaseTest,
):
    """Test the contribution skill with only one agent."""

    agent_package = "valory/contribution:0.1.0"
    skill_package = "valory/contribution_skill_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR
