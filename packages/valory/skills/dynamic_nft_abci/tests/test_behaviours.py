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
from typing import Any, Dict, Hashable, Optional, Type

import pytest
from valory.skills.dynamic_nft_abci.behaviours import (  # type: ignore
    DBUpdateBehaviour,
    DynamicNFTBaseBehaviour,
    ImageCodeCalculationBehaviour,
    ImageGenerationBehaviour,
    ImagePushBehaviour,
    NewMemberListBehaviour,
    NewMemberUpdateBehaviour,
    ObservationBehaviour,
)
from valory.skills.dynamic_nft_abci.rounds import (  # type: ignore
    Event,
    SynchronizedData,
)

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)


@dataclass
class BehaviourTestCase:
    """BehaviourTestCase"""

    initial_data: Dict[str, Hashable]
    event: Event


class BaseDynamicNFTTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parent.parent

    behaviour: DynamicNFTBaseBehaviour
    behaviour_class: Type[DynamicNFTBaseBehaviour]
    next_behaviour_class: Type[DynamicNFTBaseBehaviour]
    synchronized_data: SynchronizedData
    done_event = Event.DONE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert self.behaviour.behaviour_id == self.behaviour_class.behaviour_id

    def complete(self, event: Event) -> None:
        """Complete test"""

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert self.behaviour.behaviour_id == self.next_behaviour_class.behaviour_id


class TestDBUpdateBehaviour(BaseDynamicNFTTest):
    """Tests DBUpdateBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = DBUpdateBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestImageCodeCalculationBehaviour(BaseDynamicNFTTest):
    """Tests ImageCodeCalculationBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = ImageCodeCalculationBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestImageGenerationBehaviour(BaseDynamicNFTTest):
    """Tests ImageGenerationBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = ImageGenerationBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestImagePushBehaviour(BaseDynamicNFTTest):
    """Tests ImagePushBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = ImagePushBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestNewMemberListBehaviour(BaseDynamicNFTTest):
    """Tests NewMemberListBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = NewMemberListBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestNewMemberUpdateBehaviour(BaseDynamicNFTTest):
    """Tests NewMemberUpdateBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = NewMemberUpdateBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)


class TestObservationBehaviour(BaseDynamicNFTTest):
    """Tests ObservationBehaviour"""

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = ObservationBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = BaseBehaviour  # TODO: set the correct value

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)
