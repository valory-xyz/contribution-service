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
from packages.valory.skills.dynamic_nft_abci.behaviours import DUMMY_MEMBER_TO_NFT_URI
from packages.valory.skills.dynamic_nft_abci.payloads import NewMembersPayload
from packages.valory.skills.dynamic_nft_abci.rounds import (
    Event,
    NewMembersRound,
    SynchronizedData,
)


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_dummy_new_members_payload() -> str:
    """Dummy new members payload"""
    return json.dumps(DUMMY_MEMBER_TO_NFT_URI, sort_keys=True)


def get_new_members_payload(
    participants: FrozenSet[str],
    new_members: Optional[str],
) -> Mapping[str, BaseTxPayload]:
    """Get new members payloads."""
    return {
        participant: NewMembersPayload(participant, new_members)
        for participant in participants
    }


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
                payloads=get_new_members_payload(
                    participants=get_participants(),
                    new_members=get_dummy_new_members_payload(),
                ),
                final_data={
                    "members": get_dummy_new_members_payload(),
                    "most_voted_new_members": get_dummy_new_members_payload(),
                },
                event=Event.DONE,
                most_voted_payload=get_dummy_new_members_payload(),
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
