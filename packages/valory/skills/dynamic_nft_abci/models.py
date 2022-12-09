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

from enum import Enum
from time import time
from typing import Any, Dict, Optional

import pygsheets
from aea.skills.base import Model

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.dynamic_nft_abci.rounds import DynamicNFTAbciApp


DEFAULT_ADDRESS = "0x0000000000000000000000000000000000000000"
DEFAULT_POINTS = 0
VERIFICATION_POINTS = 100
INSERT_ROW_INDEX = 2  # header is 1


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
        self.leaderboard_points_range = self._ensure("leaderboard_points_range", kwargs)
        self.leaderboard_layers_range = self._ensure("leaderboard_layers_range", kwargs)
        leaderboard_api_key = kwargs.pop("leaderboard_api_key", None)
        self.leaderboard_endpoint = (
            f"{leaderboard_base_endpoint}/{leaderboard_sheet_id}/values:batchGet?"
            f"ranges={self.leaderboard_points_range}&ranges={self.leaderboard_layers_range}&key={leaderboard_api_key}"
        )
        self.whitelist_api_key = kwargs.pop("whitelist_api_key", None)
        self.whitelist_endpoint = self._ensure("whitelist_endpoint", kwargs)
        self.dynamic_contribution_contract_address = self._ensure(
            "dynamic_contribution_contract_address", kwargs
        )
        self.token_uri_base = self._ensure("token_uri_base", kwargs)
        self.ipfs_gateway_base_url = self._ensure("ipfs_gateway_base_url", kwargs)
        self.basic_image_cid = self._ensure("basic_image_cid", kwargs)
        self.earliest_block_to_monitor = self._ensure(
            "earliest_block_to_monitor", kwargs
        )

        super().__init__(*args, **kwargs)


class Sheet(Model):
    """A model to handle Google Sheet interactions."""

    class WalletStatus(Enum):
        """Represents wallet status."""

        LINKED = "linked"
        UNLINKED = "unlinked"
        LINKING = "linking"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize GoogleSheets model."""
        self.api = pygsheets.authorize(
            service_file=self.ensure("auth_file_path", kwargs)
        )
        self.leaderboard_sheet_id = self.ensure("leaderboard_sheet_id", kwargs)
        self.leaderboard_sheet_name = self.ensure("leaderboard_sheet_name", kwargs)
        self.sheet = self.api.open_by_key(self.leaderboard_sheet_id).worksheet(
            "title", self.leaderboard_sheet_name
        )
        self.name_col = self.ensure("name_col", kwargs)
        self.address_col = self.ensure("address_col", kwargs)
        self.points_col = self.ensure("points_col", kwargs)
        self.discord_id_col = self.ensure("discord_id_col", kwargs)
        self.observation_interval = self.ensure("observation_interval", kwargs)
        self.linking_wallets = {}

        super().__init__(*args, **kwargs)

    def ensure(self, keyword: str, kwargs: Dict) -> Any:
        """Ensure a keyword argument."""
        value = kwargs.pop(keyword, None)
        if value is None:
            raise ValueError(
                f"Value for {keyword} is required by {self.__class__.__name__}."
            )
        return value

    def create(self, discord_id, name, address=DEFAULT_ADDRESS):
        """Create a new user."""
        # Add a new blank line after row 1
        self.sheet.insert_rows(row=1, number=1)
        # Add the correct values
        self.sheet.update_value((INSERT_ROW_INDEX, self.discord_id_col), discord_id)
        self.sheet.update_value((INSERT_ROW_INDEX, self.address_col), address)
        self.sheet.update_value((INSERT_ROW_INDEX, self.name_col), name)
        self.sheet.update_value((INSERT_ROW_INDEX, self.points_col), DEFAULT_POINTS)

    def row_to_dict(self, row):
        """Returns the data for a specific formatted for the HTTP response"""
        return {
            "name": row[self.name_col - 1],
            "address": row[self.address_col - 1],
            "points": row[self.points_col - 1],
            "discord_id": row[self.discord_id_col - 1],
        }

    def read(self, discord_id=None, address=None):
        """Read the leaderboard or one specific entry by id or address."""
        # Get the leaderboard
        rows = self.sheet.get_all_values(returnas="matrix")

        # Get the whole leaderboard
        if discord_id is None and address is None:
            # Skip empty rows
            rows = filter(lambda row: not all(i == "" for i in row), rows)
            # Get the first 4 columns only
            rows = [row[:4] for row in rows]
            # Return the data, skipping the header row
            return [self.row_to_dict(row) for row in rows[1:]]

        # Get a specific entry
        for row in rows:
            if row[self.discord_id_col - 1] == discord_id and discord_id is not None:
                return row
            if row[self.address_col - 1] == address and address is not None:
                return row
        return None

    def update(self, discord_id, address):
        """Updates an entry in the leaderboard"""
        rows = self.sheet.get_all_values(returnas="matrix")
        for i, row in enumerate(rows):
            row_index = i + 1
            if row[self.discord_id_col - 1] == discord_id:
                self.sheet.update_value((row_index, self.address_col), address)
                self.sheet.update_value(
                    (row_index, self.points_col), VERIFICATION_POINTS
                )
                break

    def delete(self, discord_id):
        """Removes an user entry"""
        rows = self.sheet.get_all_values(returnas="matrix")
        for i, row in enumerate(rows):
            if row[self.discord_id_col - 1] == discord_id:
                self.sheet.delete_rows(i + 1)
                break

    def write(
        self,
        discord_id: str,
        wallet_address: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Writes an entry to the sheet."""
        user = self.read(discord_id)
        if not user:
            self.create(discord_id, name)
        else:
            self.update(
                discord_id=user[self.discord_id_col - 1],
                address=wallet_address or user[self.address_col - 1],
            )
        # Since this data is not subject to consensus we can safely use time() here
        self.linking_wallets[wallet_address] = time()

    def get_wallet_status(self, wallet_address: str):
        """Checks the wallet linking status"""
        user = self.read(address=wallet_address)
        if user is None:
            return self.WalletStatus.UNLINKED.value

        # Since this data is not subject to consensus we can safely use time() here
        if (
            wallet_address in self.linking_wallets
            and time() - self.linking_wallets[wallet_address]
            < self.observation_interval
        ):
            return self.WalletStatus.LINKING.value

        self.linking_wallets.pop(wallet_address, None)
        return self.WalletStatus.LINKED.value


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
