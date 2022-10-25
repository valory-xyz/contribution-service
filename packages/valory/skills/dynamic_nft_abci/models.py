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

"""This module contains the shared state for the abci skill of DynamicNFTAbciApp."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.dynamic_nft_abci.rounds import DynamicNFTAbciApp


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=DynamicNFTAbciApp, **kwargs)


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.ipfs_domain_name = self._ensure("ipfs_domain_name", kwargs)
        leaderboard_base_endpoint = self._ensure("leaderboard_base_endpoint", kwargs)
        leaderboard_sheet_id = self._ensure("leaderboard_sheet_id", kwargs)
        leaderboard_cell_range = self._ensure("cell_range", kwargs)
        leaderboard_api_key = self._ensure("leaderboard_api_key", kwargs)
        self.leaderboard_endpoint = (
            f"{leaderboard_base_endpoint}/{leaderboard_sheet_id}/values/{leaderboard_cell_range}?key={leaderboard_api_key}"
        )

        super().__init__(*args, **kwargs)


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
