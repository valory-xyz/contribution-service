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

"""Test the models.py module of the DynamicNFT skill."""

from typing import Any
from unittest import mock

from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
from packages.valory.skills.dynamic_nft_abci.models import (
    DEFAULT_ADDRESS,
    SharedState,
    Sheet,
    VERIFICATION_POINTS,
)


class TestSharedState:  # pylint: disable=too-few-public-methods
    """Test SharedState of DynamicNFT skill."""

    def test_initialization(  # pylint: disable=no-self-use
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())


class DummySheetApi:
    class DummySheet:
        def __init__(self) -> None:
            self.values = [
                ["dummy_header", "dummy_header", "dummy_header", "dummy_header"]
            ]

        def worksheet(self, title, leaderboard_sheet_name):
            """Dummy worksheet"""
            return self

        def get_all_values(self, returnas="matrix"):
            """Dummy get_all_values"""
            return self.values

        def insert_rows(self, row, number, values):
            """Dummy insert_rows"""
            for i in range(row, row + number):
                self.values.insert(i, values)

        def delete_rows(self, row_index):
            """Dummy delete_rows"""
            row_index = row_index - 1
            del self.values[row_index]

        def update_value(self, row_col, new_value):
            """Dummy update_value"""
            row, col = row_col
            row -= 1
            col -= 1
            self.values[row][col] = new_value

    def open_by_key(self, leaderboard_sheet_id):
        return self.DummySheet()


class TestSheet:
    """Test Sheet of DynamicNFT skill."""

    @mock.patch("pygsheets.authorize", return_value=DummySheetApi())
    def setup(self, *_mocks: Any, **kwargs: Any) -> None:
        """Setup test"""
        self.sheet = Sheet(
            name="dummy_sheet_model",
            auth_file_path="dummy_auth_file_path",
            leaderboard_sheet_id="dummy_leaderboard_sheet_id",
            leaderboard_sheet_name="dummy_leaderboard_sheet_name",
            name_col=1,
            address_col=2,
            points_col=3,
            discord_id_col=4,
            observation_interval=10,
            skill_context=DummyContext(),
        )

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        pass

    def test_create(self):
        """Test create"""
        self.sheet.create(discord_id="dummy_discord_id", name="dummy_name")
        assert self.sheet.read() == [
            {
                "name": "dummy_name",
                "address": "0x0000000000000000000000000000000000000000",
                "points": 0,
                "discord_id": "dummy_discord_id",
            }
        ]

    def test_read(self):
        """Test read"""
        assert self.sheet.read() == []

    def test_update(self):
        """Test update"""
        self.sheet.create(discord_id="dummy_discord_id", name="dummy_name")
        self.sheet.update(discord_id="dummy_discord_id", address="new_address")
        assert self.sheet.read() == [
            {
                "name": "dummy_name",
                "address": "new_address",
                "points": VERIFICATION_POINTS,
                "discord_id": "dummy_discord_id",
            }
        ]

    def test_delete(self):
        """Test delete"""
        self.sheet.create(discord_id="dummy_discord_id", name="dummy_name")
        self.sheet.delete("dummy_discord_id")
        assert self.sheet.read() == []

    def test_write(self):
        """Test write"""
        self.sheet.write(discord_id="dummy_discord_id", name="dummy_name")
        assert self.sheet.read() == [
            {
                "name": "dummy_name",
                "address": DEFAULT_ADDRESS,
                "points": 0,
                "discord_id": "dummy_discord_id",
            }
        ]

    def test_write_with_address(self):
        """Test write"""
        self.sheet.create(discord_id="dummy_discord_id", name="dummy_name")
        self.sheet.write(discord_id="dummy_discord_id", wallet_address="dummy_address")
        assert self.sheet.read() == [
            {
                "name": "dummy_name",
                "address": "dummy_address",
                "points": VERIFICATION_POINTS,
                "discord_id": "dummy_discord_id",
            }
        ]
        assert "dummy_address" in self.sheet.linking_wallets

    def test_get_wallet_status(self):
        """Test get_wallet_status"""
        # Empty database
        assert (
            self.sheet.get_wallet_status("dummy_wallet_address")
            == self.sheet.WalletStatus.UNLINKED.value
        )
        # Add an entry and check its wallet it is linking
        self.sheet.write(discord_id="dummy_discord_id", wallet_address=DEFAULT_ADDRESS)
        assert DEFAULT_ADDRESS in self.sheet.linking_wallets
        assert (
            self.sheet.get_wallet_status(DEFAULT_ADDRESS)
            == self.sheet.WalletStatus.LINKING.value
        )
        # Change the wallet's linking time and check it is linked now
        self.sheet.linking_wallets[DEFAULT_ADDRESS] = 30
        assert (
            self.sheet.get_wallet_status(DEFAULT_ADDRESS)
            == self.sheet.WalletStatus.LINKED.value
        )
