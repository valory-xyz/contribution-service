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
from packages.valory.skills.dynamic_nft_abci.models import SharedState, Sheet


class TestSharedState:  # pylint: disable=too-few-public-methods
    """Test SharedState of DynamicNFT skill."""

    def test_initialization(  # pylint: disable=no-self-use
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())


class TestSheet:
    """Test Sheet of DynamicNFT skill."""

    class DummySheetApi:
        class DummySheet:
            def __init__(self) -> None:
                self.values = [
                    ["dummy_header", "dummy_header", "dummy_header", "dummy_header"]
                ]

            def worksheet(self, title, leaderboard_sheet_name):
                return self

            def get_all_values(self, returnas="matrix"):
                return self.values

            def insert_rows(self, row, number, values):
                for i in range(row, row + number):
                    self.values.insert(i, values)

        def open_by_key(self, leaderboard_sheet_id):
            return self.DummySheet()

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
            observation_interval="dummy_observation_interval",
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
