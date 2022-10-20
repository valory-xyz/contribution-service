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

"""This package contains the tests for rounds of DynamicNFTAbciApp."""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, Hashable, List, Mapping, Optional

import pytest

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.dynamic_nft_abci.behaviours import (
    DUMMY_LEADERBOARD,
    DUMMY_MEMBER_TO_NFT_URI,
)
from packages.valory.skills.dynamic_nft_abci.payloads import (
    ImageCodeCalculationPayload,
    LeaderboardObservationPayload,
    NewMembersPayload,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    Event,
    ImageCodeCalculationRound,
    LeaderboardObservationRound,
    NewMembersRound,
    SynchronizedData,
)


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_payloads(
    payload_cls: BaseTxPayload,
    data: Optional[str],
) -> Mapping[str, BaseTxPayload]:
    """Get payloads."""
    return {
        participant: payload_cls(participant, data)
        for participant in get_participants()
    }


def get_dummy_new_members_payload_serialized() -> str:
    """Dummy new members payload"""
    return json.dumps(DUMMY_MEMBER_TO_NFT_URI, sort_keys=True)


def get_dummy_leaderboard_payload_serialized() -> str:
    """Dummy leaderboard payload"""
    return json.dumps(DUMMY_LEADERBOARD, sort_keys=True)


def get_image_code_calculation_payload_serialized() -> str:
    """Dummy image code calculation payload"""
    data = {
        "member_a": {"points": 100, "image_code": "dummy_image_code_a"},
        "member_b": {"points": 200, "image_code": "dummy_image_code_b"},
        "member_c": {"points": 300, "image_code": "dummy_image_code_c"},
    }
    return json.dumps(data, sort_keys=True)


@dataclass
class RoundTestCase:
    """RoundTestCase"""

    initial_data: Dict[str, Hashable]
    payloads: Mapping[str, BaseTxPayload]
    final_data: Dict[str, Hashable]
    event: Event
    most_voted_payload: Any
    synchronized_data_attr_checks: List[Callable] = field(default_factory=list)


MAX_PARTICIPANTS: int = 4


class BaseDynamicNFTRoundTestClass(BaseCollectSameUntilThresholdRoundTest):
    """Base test class for DynamicNFT rounds."""

    synchronized_data: SynchronizedData
    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def run_test(self, test_case: RoundTestCase, **kwargs: Any) -> None:
        """Run the test"""

        self.synchronized_data.update(**test_case.initial_data)

        test_round = self.round_class(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=test_case.payloads,
                synchronized_data_update_fn=lambda sync_data, _: sync_data.update(
                    **test_case.final_data
                ),
                synchronized_data_attr_checks=test_case.synchronized_data_attr_checks,
                most_voted_payload=test_case.most_voted_payload,
                exit_event=test_case.event,
            )
        )


class TestNewMembersRound(BaseDynamicNFTRoundTestClass):
    """Tests for NewMemberListRound."""

    round_class = NewMembersRound

    @pytest.mark.parametrize(
        "test_case",
        (
            RoundTestCase(
                initial_data={},
                payloads=get_payloads(
                    payload_cls=NewMembersPayload,
                    data=get_dummy_new_members_payload_serialized(),
                ),
                final_data={
                    "members": json.loads(get_dummy_new_members_payload_serialized()),
                    "most_voted_new_members": json.loads(
                        get_dummy_new_members_payload_serialized()
                    ),
                },
                event=Event.DONE,
                most_voted_payload=get_dummy_new_members_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.members,
                    lambda _synchronized_data: _synchronized_data.most_voted_new_members,
                ],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)


class TestLeaderboardObservationRound(BaseDynamicNFTRoundTestClass):
    """Tests for LeaderboardObservationRound."""

    round_class = LeaderboardObservationRound

    @pytest.mark.parametrize(
        "test_case",
        (
            RoundTestCase(
                initial_data={},
                payloads=get_payloads(
                    payload_cls=LeaderboardObservationPayload,
                    data=get_dummy_leaderboard_payload_serialized(),
                ),
                final_data={
                    "most_voted_leaderboard": json.loads(
                        get_dummy_leaderboard_payload_serialized()
                    ),
                },
                event=Event.DONE,
                most_voted_payload=get_dummy_leaderboard_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.most_voted_leaderboard,
                ],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)


class TestImageCodeCalculationRound(BaseDynamicNFTRoundTestClass):
    """Tests for ImageCodeCalculationRound."""

    round_class = ImageCodeCalculationRound

    @pytest.mark.parametrize(
        "test_case",
        (
            RoundTestCase(
                initial_data={},
                payloads=get_payloads(
                    payload_cls=ImageCodeCalculationPayload,
                    data=get_image_code_calculation_payload_serialized(),
                ),
                final_data={
                    "most_voted_updates": json.loads(
                        get_image_code_calculation_payload_serialized()
                    ),
                },
                event=Event.DONE,
                most_voted_payload=get_image_code_calculation_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.most_voted_updates,
                ],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)
