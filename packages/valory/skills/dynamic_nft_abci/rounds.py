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

"""This package contains the rounds of DynamicNFTAbciApp."""

import json
from abc import ABC
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    EventToTimeout,
    TransactionType,
)
from packages.valory.skills.dynamic_nft_abci.payloads import (
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    ImagePushPayload,
    LeaderboardObservationPayload,
    NewMembersPayload,
)


class Event(Enum):
    """DynamicNFTAbciApp Events"""

    NO_MAJORITY = "no_majority"
    NO_NEW_IMAGES = "no_new_images"
    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def members(self) -> dict:
        """Get the member table."""
        return cast(dict, self.db.get("members", {}))

    @property
    def images(self) -> dict:
        """Get the image table."""
        return cast(dict, self.db.get("images", {}))

    @property
    def redirects(self) -> dict:
        """Get the redirect table."""
        return cast(dict, self.db.get("redirects", {}))

    @property
    def most_voted_new_members(self) -> Dict:
        """Get the most_voted_new_members."""
        return cast(Dict, self.db.get_strict("most_voted_new_members"))

    @property
    def most_voted_leaderboard(self) -> Dict:
        """Get the most_voted_leaderboard."""
        return cast(Dict, self.db.get_strict("most_voted_leaderboard"))

    @property
    def most_voted_updates(self) -> Dict:
        """Get the most_voted_updates."""
        return cast(Dict, self.db.get_strict("most_voted_updates"))


class DynamicNFTABCIAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the Dynamic NFT ABCI skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, self._synchronized_data)


class NewMembersRound(CollectSameUntilThresholdRound, DynamicNFTABCIAbstractRound):
    """NewMemberListRound"""

    round_id: str = "new_members"
    allowed_tx_type = NewMembersPayload.transaction_type
    payload_attribute: str = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            # Add the new members to the members table. Note that the new members have no points or image_code fields
            members = {
                **json.loads(self.most_voted_payload),
                **self.synchronized_data.members,
            }
            synchronized_data = self.synchronized_data.update(
                members=members,
                most_voted_new_members=json.loads(self.most_voted_payload),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class LeaderboardObservationRound(
    CollectSameUntilThresholdRound, DynamicNFTABCIAbstractRound
):
    """LeaderboardObservationRound"""

    round_id = "leaderboard_observation"
    allowed_tx_type = LeaderboardObservationPayload.transaction_type
    payload_attribute = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                most_voted_leaderboard=json.loads(self.most_voted_payload),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ImageCodeCalculationRound(
    CollectSameUntilThresholdRound, DynamicNFTABCIAbstractRound
):
    """ImageCodeCalculationRound"""

    round_id: str = "image_code_calculation"
    allowed_tx_type = ImageCodeCalculationPayload.transaction_type
    payload_attribute = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                most_voted_updates=json.loads(self.most_voted_payload),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ImageGenerationRound(CollectSameUntilThresholdRound, DynamicNFTABCIAbstractRound):
    """ImageGenerationRound"""

    round_id: str = "image_generation"
    allowed_tx_type = ImageGenerationPayload.transaction_type
    payload_attribute: str = ImageGenerationPayload.transaction_type
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        Event.NO_MAJORITY, Event.NO_NEW_IMAGES, Event.DONE
        raise NotImplementedError

    def check_payload(self, payload: ImageGenerationPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: ImageGenerationPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class ImagePushRound(AbstractRound):
    """ImagePushRound"""

    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str = "image_push"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str = ImagePushPayload.transaction_type

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        Event.NO_MAJORITY, Event.DONE
        raise NotImplementedError

    def check_payload(self, payload: ImagePushPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: ImagePushPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class DBUpdateRound(AbstractRound):
    """DBUpdateRound"""

    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str = "db_update"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str = DBUpdatePayload.transaction_type

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        Event.NO_MAJORITY, Event.DONE
        raise NotImplementedError

    def check_payload(self, payload: DBUpdatePayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: DBUpdatePayload) -> None:
        """Process payload."""
        raise NotImplementedError


class FinishedDBUpdateRound(DegenerateRound):
    """FinishedDBUpdateRound"""

    round_id: str = "finished_db_update"


class DynamicNFTAbciApp(AbciApp[Event]):
    """DynamicNFTAbciApp"""

    initial_round_cls: AppState = NewMembersRound
    initial_states: Set[AppState] = {NewMembersRound}
    transition_function: AbciAppTransitionFunction = {
        NewMembersRound: {
            Event.DONE: LeaderboardObservationRound,
            Event.NO_MAJORITY: NewMembersRound,
            Event.ROUND_TIMEOUT: NewMembersRound,
        },
        LeaderboardObservationRound: {
            Event.DONE: ImageCodeCalculationRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        ImageCodeCalculationRound: {
            Event.DONE: ImageGenerationRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        ImageGenerationRound: {
            Event.DONE: ImagePushRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
            Event.NO_NEW_IMAGES: DBUpdateRound,
        },
        ImagePushRound: {
            Event.DONE: DBUpdateRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        DBUpdateRound: {
            Event.DONE: FinishedDBUpdateRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        FinishedDBUpdateRound: {},
    }
    final_states: Set[AppState] = {FinishedDBUpdateRound}
    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys: List[str] = []
