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
from packages.valory.skills.dynamic_nft_abci.payloads import (
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    LeaderboardObservationPayload,
    NewMembersPayload,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    DBUpdateRound,
    Event,
    ImageCodeCalculationRound,
    ImageGenerationRound,
    LeaderboardObservationRound,
    NewMembersRound,
    SynchronizedData,
)
from packages.valory.skills.dynamic_nft_abci.tests.test_behaviours import (
    DUMMY_LEADERBOARD,
)


TOKEN_URI_BASE = "https://pfp.autonolas.network/series/1/"  # nosec

DUMMY_MEMBER_TO_NFT_URI = {
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A": f"{TOKEN_URI_BASE}/1",
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525": f"{TOKEN_URI_BASE}2",
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7": f"{TOKEN_URI_BASE}3",
    "0x19B043aD06C48aeCb2028B0f10503422BD0E0918": f"{TOKEN_URI_BASE}4",
    "0x8325c5e4a56E352355c590E4A43420840F067F98": f"{TOKEN_URI_BASE}5",  # this one does not appear in the dummy leaderboard
}


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


def get_dummy_new_members_payload_error_serialized() -> str:
    """Dummy new members payload"""
    return json.dumps({"error": True}, sort_keys=True)


def get_dummy_leaderboard_payload_serialized(api_error: bool = False) -> str:
    """Dummy leaderboard payload"""
    if api_error:
        return json.dumps({})
    return json.dumps(DUMMY_LEADERBOARD, sort_keys=True)


def get_image_code_calculation_payload_serialized() -> str:
    """Dummy image code calculation payload"""
    data = {
        "member_a": {"points": 100, "image_code": "dummy_image_code_a"},
        "member_b": {"points": 200, "image_code": "dummy_image_code_b"},
        "member_c": {"points": 300, "image_code": "dummy_image_code_c"},
    }
    return json.dumps(data, sort_keys=True)


def get_dummy_members() -> str:
    """Dummy members table"""
    data = {
        "member_a": {"points": 100, "image_code": "dummy_image_code_a", "uri": "uri_1"},
        "member_b": {"points": 200, "image_code": "dummy_image_code_b", "uri": "uri_2"},
        "member_c": {"points": 300, "image_code": "dummy_image_code_c", "uri": "uri_3"},
    }
    return json.dumps(data, sort_keys=True)


def get_dummy_images() -> dict:
    """Dummy image table"""
    return {
        "dummy_image_code_a": "uri_1",
        "dummy_image_code_b": "uri_2",
        "dummy_image_code_c": "uri_3",
    }


def get_image_generation_payload_serialized(status: str = "success") -> str:
    """Dummy image generation payload"""

    DUMMY_NEW_IMAGE_CODE_TO_HASHES = {
        "000000": "dummy_hash_1",
        "010101": "dummy_hash_2",
        "020202": "dummy_hash_3",
    }

    return json.dumps(
        {
            "new_image_code_to_hashes": DUMMY_NEW_IMAGE_CODE_TO_HASHES,
            "status": status,
        },
        sort_keys=True,
    )


def get_db_update_payload_serialized() -> str:
    """Dummy db update payload"""
    return json.dumps({}, sort_keys=True)


@dataclass
class RoundTestCase:
    """RoundTestCase"""

    name: str
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
                name="Happy path",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=NewMembersPayload,
                    data=get_dummy_new_members_payload_serialized(),
                ),
                final_data={
                    "members": json.loads(get_dummy_new_members_payload_serialized()),
                },
                event=Event.DONE,
                most_voted_payload=get_dummy_new_members_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.members,
                ],
            ),
            RoundTestCase(
                name="Contract error",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=NewMembersPayload,
                    data=get_dummy_new_members_payload_error_serialized(),
                ),
                final_data={
                    "members": json.loads(
                        get_dummy_new_members_payload_error_serialized()
                    ),
                },
                event=Event.CONTRACT_ERROR,
                most_voted_payload=get_dummy_new_members_payload_error_serialized(),
                synchronized_data_attr_checks=[],
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
                name="Happy path",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=LeaderboardObservationPayload,
                    data=get_dummy_leaderboard_payload_serialized(),
                ),
                final_data={
                    "most_voted_api_data": json.loads(
                        get_dummy_leaderboard_payload_serialized()
                    ),
                },
                event=Event.DONE,
                most_voted_payload=get_dummy_leaderboard_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.most_voted_api_data,
                ],
            ),
            RoundTestCase(
                name="Api error",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=LeaderboardObservationPayload,
                    data=get_dummy_leaderboard_payload_serialized(api_error=True),
                ),
                final_data={},
                event=Event.API_ERROR,
                most_voted_payload=get_dummy_leaderboard_payload_serialized(
                    api_error=True
                ),
                synchronized_data_attr_checks=[],
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
                name="Happy path",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=ImageCodeCalculationPayload,
                    data=get_image_code_calculation_payload_serialized(),
                ),
                final_data={
                    "most_voted_member_updates": json.loads(
                        get_image_code_calculation_payload_serialized()
                    ),
                },
                event=Event.DONE,
                most_voted_payload=get_image_code_calculation_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.most_voted_member_updates,
                ],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)


class TestImageGenerationRound(BaseDynamicNFTRoundTestClass):
    """Tests for ImageGenerationRound."""

    round_class = ImageGenerationRound

    @pytest.mark.parametrize(
        "test_case",
        (
            RoundTestCase(
                name="Happy path",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=ImageGenerationPayload,
                    data=get_image_generation_payload_serialized("success"),
                ),
                final_data={
                    "images": json.loads(
                        get_image_generation_payload_serialized("success")
                    )["new_image_code_to_hashes"],
                },
                event=Event.DONE,
                most_voted_payload=get_image_generation_payload_serialized("success"),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.images,
                ],
            ),
            RoundTestCase(
                name="Happy path",
                initial_data={},
                payloads=get_payloads(
                    payload_cls=ImageGenerationPayload,
                    data=get_image_generation_payload_serialized("error"),
                ),
                final_data={},
                event=Event.IMAGE_ERROR,
                most_voted_payload=get_image_generation_payload_serialized("error"),
                synchronized_data_attr_checks=[],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)


class TestDBUpdateRound(BaseDynamicNFTRoundTestClass):
    """Tests for DBUpdateRound."""

    round_class = DBUpdateRound

    @pytest.mark.parametrize(
        "test_case",
        (
            RoundTestCase(
                name="Happy path",
                initial_data={
                    "members": json.loads(get_dummy_members()),
                    "images": get_dummy_images(),
                    "redirects": {},
                    "most_voted_member_updates": json.loads(get_dummy_members()),
                },
                payloads=get_payloads(
                    payload_cls=DBUpdatePayload,
                    data=get_db_update_payload_serialized(),
                ),
                final_data={
                    "images": get_dummy_images(),
                },
                event=Event.DONE,
                most_voted_payload=get_db_update_payload_serialized(),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.images,
                ],
            ),
        ),
    )
    def test_run(self, test_case: RoundTestCase) -> None:
        """Run tests."""
        self.run_test(test_case)
