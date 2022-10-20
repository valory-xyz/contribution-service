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

"""This package contains round behaviours of DynamicNFTAbciApp."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.dynamic_nft_abci.behaviours import (
    DBUpdateBehaviour,
    DUMMY_LEADERBOARD,
    DynamicNFTBaseBehaviour,
    ImageCodeCalculationBehaviour,
    ImageGenerationBehaviour,
    LeaderboardObservationBehaviour,
    NewMembersBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.rounds import Event, SynchronizedData


def get_dummy_updates() -> Dict:
    """Dummy updates"""
    return {
        "dummy_member_1": {"points": 100, "image_code": "000100"},
        "dummy_member_2": {"points": 200, "image_code": "000102"},
    }


@dataclass
class BehaviourTestCase:
    """BehaviourTestCase"""

    name: str
    initial_data: Dict[str, Any]
    event: Event
    next_behaviour_class: Optional[Type[DynamicNFTBaseBehaviour]] = None


class BaseDynamicNFTTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parent.parent

    behaviour: DynamicNFTBaseBehaviour  # type: ignore
    behaviour_class: Type[DynamicNFTBaseBehaviour]
    next_behaviour_class: Type[DynamicNFTBaseBehaviour]
    synchronized_data: SynchronizedData
    done_event = Event.DONE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,  # type: ignore
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.behaviour_class.behaviour_id
        )

    def complete(self, event: Event) -> None:
        """Complete test"""

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )


class TestNewMembersBehaviour(BaseDynamicNFTTest):
    """Tests NewMembersBehaviour"""

    behaviour_class = NewMembersBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)


class TestLeaderboardObservationBehaviour(BaseDynamicNFTTest):
    """Tests LeaderboardObservationBehaviour"""

    behaviour_class = LeaderboardObservationBehaviour
    next_behaviour_class = ImageCodeCalculationBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)


class TestImageCodeCalculationBehaviour(BaseDynamicNFTTest):
    """Tests ImageCodeCalculationBehaviour"""

    behaviour_class = ImageCodeCalculationBehaviour
    next_behaviour_class = ImageGenerationBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(most_voted_leaderboard=DUMMY_LEADERBOARD),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)

    @pytest.mark.parametrize(
        "points, expected_code",
        [
            (0, "000000"),
            (150, "000000"),
            (999, "000000"),
            (1000, "000100"),
            (1999, "000102"),
            (2000, "000200"),
            (3750, "000302"),
            (10000, "000302"),
        ],
    )
    def test_points_to_code(self, points: float, expected_code: str) -> None:
        """Test the points_to_code function"""
        assert ImageCodeCalculationBehaviour.points_to_code(points) == expected_code

    def test_points_to_code_negative(self) -> None:
        """Test the points_to_code function"""
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(-100)


class TestImageGenerationBehaviour(BaseDynamicNFTTest):
    """Tests ImageGenerationBehaviour"""

    behaviour_class = ImageGenerationBehaviour
    next_behaviour_class = DBUpdateBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(most_voted_updates=get_dummy_updates()),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)
