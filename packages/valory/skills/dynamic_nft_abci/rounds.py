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
    LeaderboardObservationPayload,
    NewMembersPayload,
)


class Event(Enum):
    """DynamicNFTAbciApp Events"""

    NO_MAJORITY = "no_majority"
    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    IMAGE_ERROR = "image_error"
    API_ERROR = "api_error"
    CONTRACT_ERROR = "contract_error"


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
    def most_voted_api_data(self) -> Dict:
        """Get the most_voted_api_data."""
        return cast(Dict, self.db.get_strict("most_voted_api_data"))

    @property
    def most_voted_member_updates(self) -> Dict:
        """Get the most_voted_member_updates."""
        return cast(Dict, self.db.get_strict("most_voted_member_updates"))


class ContributionAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the APY estimation skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)


class NewMembersRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """NewMemberListRound"""

    round_id: str = "new_members"
    allowed_tx_type = NewMembersPayload.transaction_type
    payload_attribute: str = "content"
    synchronized_data_class = SynchronizedData

    ERROR_PAYLOAD = {"error": True}

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            # Add the new members to the members table. Note that the new members have no points or image_code fields
            new_member_to_uri = json.loads(self.most_voted_payload)

            if new_member_to_uri == NewMembersRound.ERROR_PAYLOAD:
                return self.synchronized_data, Event.CONTRACT_ERROR

            members = {
                **new_member_to_uri,
                **self.synchronized_data.members,
            }

            # Create redirects for new members
            new_redirects = {}
            for uri in new_member_to_uri.values():
                new_redirects[uri] = uri

            redirects = {
                **new_redirects,
                **self.synchronized_data.redirects,
            }

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                members=members,
                redirects=redirects,
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class LeaderboardObservationRound(
    ContributionAbstractRound, CollectSameUntilThresholdRound
):
    """LeaderboardObservationRound"""

    round_id = "leaderboard_observation"
    allowed_tx_type = LeaderboardObservationPayload.transaction_type
    payload_attribute = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            payload = json.loads(self.most_voted_payload)
            if payload == {}:
                return self.synchronized_data, Event.API_ERROR

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                most_voted_api_data=payload,
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ImageCodeCalculationRound(
    ContributionAbstractRound, CollectSameUntilThresholdRound
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
                synchronized_data_class=SynchronizedData,
                most_voted_member_updates=json.loads(self.most_voted_payload),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ImageGenerationRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """ImageGenerationRound"""

    round_id: str = "image_generation"
    allowed_tx_type = ImageGenerationPayload.transaction_type
    payload_attribute = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            payload = json.loads(self.most_voted_payload)
            if payload["status"] != "success":
                return self.synchronized_data, Event.IMAGE_ERROR
            else:
                images = {
                    **self.synchronized_data.images,
                    **payload["new_image_code_to_hashes"],
                }
                synchronized_data = self.synchronized_data.update(
                    synchronized_data_class=SynchronizedData,
                    images=images,
                )
                return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class DBUpdateRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """DBUpdateRound"""

    round_id: str = "db_update"
    allowed_tx_type = DBUpdatePayload.transaction_type
    payload_attribute = "content"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:

            members = self.synchronized_data.members
            images = self.synchronized_data.images
            redirects = self.synchronized_data.redirects
            updates = self.synchronized_data.most_voted_member_updates

            for (
                member,
                data,
            ) in updates.items():
                members[member]["points"] = data["points"]
                members[member]["image_code"] = data["image_code"]

                uri = members[member]["uri"]
                redirects[uri] = images[data["image_code"]]

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                members=members,
                redirects=redirects,
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedDBUpdateRound(DegenerateRound, ABC):
    """FinishedDBUpdateRound"""

    round_id: str = "finished_db_update"


class DynamicNFTAbciApp(AbciApp[Event]):
    """DynamicNFTAbciApp"""

    initial_round_cls: AppState = NewMembersRound
    initial_states: Set[AppState] = {NewMembersRound}
    transition_function: AbciAppTransitionFunction = {
        NewMembersRound: {
            Event.DONE: LeaderboardObservationRound,
            Event.CONTRACT_ERROR: NewMembersRound,
            Event.NO_MAJORITY: NewMembersRound,
            Event.ROUND_TIMEOUT: NewMembersRound,
        },
        LeaderboardObservationRound: {
            Event.DONE: ImageCodeCalculationRound,
            Event.API_ERROR: LeaderboardObservationRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        ImageCodeCalculationRound: {
            Event.DONE: ImageGenerationRound,
            Event.NO_MAJORITY: LeaderboardObservationRound,
            Event.ROUND_TIMEOUT: LeaderboardObservationRound,
        },
        ImageGenerationRound: {
            Event.DONE: DBUpdateRound,
            Event.IMAGE_ERROR: LeaderboardObservationRound,
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
