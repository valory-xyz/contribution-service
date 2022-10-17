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

from abc import abstractmethod
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.models import Params
from packages.valory.skills.dynamic_nft_abci.rounds import (
    DBUpdateRound,
    DynamicNFTAbciApp,
    ImageCodeCalculationRound,
    ImageGenerationRound,
    ImagePushRound,
    NewMemberListRound,
    NewMemberUpdateRound,
    ObservationRound,
    SynchronizedData,
)


class DynamicNFTBaseBehaviour(BaseBehaviour):
    """Base behaviour for the common apps' skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)


class DBUpdateBehaviour(DynamicNFTBaseBehaviour):
    """DBUpdateBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "db_update"
    matching_round: Type[AbstractRound] = DBUpdateRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class ImageCodeCalculationBehaviour(DynamicNFTBaseBehaviour):
    """ImageCodeCalculationBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "image_code_calculation"
    matching_round: Type[AbstractRound] = ImageCodeCalculationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class ImageGenerationBehaviour(DynamicNFTBaseBehaviour):
    """ImageGenerationBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "image_generation"
    matching_round: Type[AbstractRound] = ImageGenerationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class ImagePushBehaviour(DynamicNFTBaseBehaviour):
    """ImagePushBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "image_push"
    matching_round: Type[AbstractRound] = ImagePushRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class NewMemberListBehaviour(DynamicNFTBaseBehaviour):
    """NewMemberListBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "new_member_list"
    matching_round: Type[AbstractRound] = NewMemberListRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class NewMemberUpdateBehaviour(DynamicNFTBaseBehaviour):
    """NewMemberUpdateBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "new_member_update"
    matching_round: Type[AbstractRound] = NewMemberUpdateRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class ObservationBehaviour(DynamicNFTBaseBehaviour):
    """ObservationBehaviour"""

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "observation"
    matching_round: Type[AbstractRound] = ObservationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class DynamicNFTRoundBehaviour(AbstractRoundBehaviour):
    """DynamicNFTRoundBehaviour"""

    initial_behaviour_cls = NewMemberListBehaviour
    abci_app_cls = DynamicNFTAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        DBUpdateBehaviour,
        ImageCodeCalculationBehaviour,
        ImageGenerationBehaviour,
        ImagePushBehaviour,
        NewMemberListBehaviour,
        NewMemberUpdateBehaviour,
        ObservationBehaviour,
    ]
