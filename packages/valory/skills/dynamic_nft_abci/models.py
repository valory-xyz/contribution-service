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

from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache, wraps
from multiprocessing import Manager
from pathlib import Path
from threading import Lock
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
CACHE_EXPIRATION_SECONDS = 10
CACHE_MAXSIZE = 128


def timed_lru_cache(seconds: int, maxsize: Optional[int] = None):
    """Timed cache"""

    def wrapper_cache(func):
        """Wrapper cache"""
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            """Wrapped func"""
            if datetime.utcnow() >= func.expiration:
                print("func.expiration lru_cache lifetime expired")
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime

            return func(*args, **kwargs)

        # Add missing methods to wrapped function
        wrapped_func.cache_clear = func.cache_clear
        wrapped_func.cache_info = func.cache_info

        return wrapped_func

    return wrapper_cache


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
        # Get the service auth string and write it to a temporal file
        service_auth = kwargs.pop("service_auth", "{}")
        service_auth_file_path = Path("/", "tmp", "service_auth.json")
        with open(service_auth_file_path, "w") as f:
            f.write(service_auth)

        # Use the file to authorize
        self.api = pygsheets.authorize(service_file=service_auth_file_path)
        self.leaderboard_sheet_id = self.ensure("leaderboard_sheet_id", kwargs)
        self.leaderboard_sheet_name = self.ensure("leaderboard_sheet_name", kwargs)
        # The following line accesses Google service to open the spreadsheet.
        # During e2e tests, this is not possible since the service auth data
        # is dummy. For this reason, we do not execute if we detect we are in an e2e test.
        self.sheet = (
            self.api.open_by_key(self.leaderboard_sheet_id).worksheet(
                "title", self.leaderboard_sheet_name
            )
            if "my_dummy_project_id" not in service_auth
            else None
        )
        self.name_col = self.ensure("name_col", kwargs)
        self.address_col = self.ensure("address_col", kwargs)
        self.points_col = self.ensure("points_col", kwargs)
        self.discord_id_col = self.ensure("discord_id_col", kwargs)
        self.observation_interval = self.ensure("observation_interval", kwargs)

        self.lock = Lock()
        manager = Manager()
        self.linking_wallets = manager.dict(lock=True)

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
        rows = self.read()
        last_entry_index = len(rows) + 1 if rows else 1  # Take the header into account

        # Build the values in the correct order: column indices are configurable
        index_to_value = {
            self.discord_id_col: discord_id,
            self.address_col: address,
            self.name_col: name,
            self.points_col: DEFAULT_POINTS,
        }
        ordered_values = [index_to_value[k] for k in sorted(index_to_value.keys())]

        # Insert the new row after last_entry_index
        self.sheet.insert_rows(row=last_entry_index, number=1, values=ordered_values)

    def row_to_dict(self, row):
        """Returns the data for a specific formatted for the HTTP response"""
        return {
            "name": row[self.name_col - 1],
            "address": row[self.address_col - 1],
            "points": row[self.points_col - 1],
            "discord_id": row[self.discord_id_col - 1],
        }

    @timed_lru_cache(seconds=CACHE_EXPIRATION_SECONDS, maxsize=CACHE_MAXSIZE)
    def _read_sheet(self):
        """Reads the sheet and returns the sheet as a matrix"""
        if self.lock.locked():
            return self.rows
        with self.lock:
            self.rows = self.sheet.get_all_values(returnas="matrix")
        return self.rows

    def read(self, discord_id=None, address=None):
        """Read the leaderboard or one specific entry by id or address."""
        # Get the leaderboard
        rows = self._read_sheet()

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
            if (
                row[self.discord_id_col - 1] == discord_id and discord_id is not None
            ) or (row[self.address_col - 1] == address and address is not None):
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

        self._read_sheet.cache_clear()

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
        with self.lock:
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

        with self.lock:
            self.linking_wallets.pop(wallet_address, None)
        return self.WalletStatus.LINKED.value


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
