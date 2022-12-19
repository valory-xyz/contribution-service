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
    get_name,
)
from packages.valory.skills.dynamic_nft_abci.payloads import (
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    LeaderboardObservationPayload,
    NewTokensPayload,
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
    def token_to_data(self) -> dict:
        """Get the token table."""
        return cast(dict, self.db.get("token_to_data", {}))

    @property
    def image_code_to_hash(self) -> dict:
        """Get the image table."""
        return cast(dict, self.db.get("image_code_to_hash", {}))

    @property
    def most_voted_api_data(self) -> Dict:
        """Get the most_voted_api_data."""
        return cast(Dict, self.db.get_strict("most_voted_api_data"))

    @property
    def most_voted_token_updates(self) -> Dict:
        """Get the most_voted_token_updates."""
        return cast(Dict, self.db.get_strict("most_voted_token_updates"))

    @property
    def last_update_time(self) -> float:
        """Get the last update time."""
        return cast(float, self.db.get("last_update_time", None))


class ContributionAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the APY estimation skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)


class NewTokensRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """NewTokensRound"""

    allowed_tx_type = NewTokensPayload.transaction_type
    payload_attribute: str = get_name(NewTokensPayload.content)
    synchronized_data_class = SynchronizedData

    ERROR_PAYLOAD = {"error": True}

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            payload = json.loads(self.most_voted_payload)

            if payload == NewTokensRound.ERROR_PAYLOAD:
                return self.synchronized_data, Event.CONTRACT_ERROR

            new_token_to_data = payload["new_token_to_data"]

            # Add the new tokens to the token table
            token_to_data = {
                **new_token_to_data,
                **self.synchronized_data.token_to_data,
            }

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(SynchronizedData.token_to_data): token_to_data
                }
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

    allowed_tx_type = LeaderboardObservationPayload.transaction_type
    payload_attribute = get_name(LeaderboardObservationPayload.content)
    synchronized_data_class = SynchronizedData

    ERROR_PAYLOAD = {}

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            payload = json.loads(self.most_voted_payload)
            if payload == LeaderboardObservationRound.ERROR_PAYLOAD:
                return self.synchronized_data, Event.API_ERROR

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(SynchronizedData.most_voted_api_data): payload
                }
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

    allowed_tx_type = ImageCodeCalculationPayload.transaction_type
    payload_attribute = get_name(ImageCodeCalculationPayload.content)
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(SynchronizedData.most_voted_token_updates): json.loads(self.most_voted_payload)
                }
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ImageGenerationRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """ImageGenerationRound"""

    allowed_tx_type = ImageGenerationPayload.transaction_type
    payload_attribute = get_name(ImageGenerationPayload.content)
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            payload = json.loads(self.most_voted_payload)
            if payload["status"] != "success":
                return self.synchronized_data, Event.IMAGE_ERROR
            else:
                image_code_to_hash = {
                    **self.synchronized_data.image_code_to_hash,
                    **payload["new_image_code_to_hash"],
                    **payload["images_in_ipfs"],
                }
                synchronized_data = self.synchronized_data.update(
                    synchronized_data_class=SynchronizedData,
                    **{
                        get_name(SynchronizedData.image_code_to_hash): image_code_to_hash
                    }
                )
                return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class DBUpdateRound(ContributionAbstractRound, CollectSameUntilThresholdRound):
    """DBUpdateRound"""

    allowed_tx_type = DBUpdatePayload.transaction_type
    payload_attribute = get_name(DBUpdatePayload.content)
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:

            token_to_data = self.synchronized_data.token_to_data
            image_code_to_hash = self.synchronized_data.image_code_to_hash
            updates = self.synchronized_data.most_voted_token_updates
            last_update_time = json.loads(self.most_voted_payload)["last_update_time"]

            for (
                token_id,
                data,
            ) in updates.items():
                token_to_data[token_id]["points"] = data["points"]
                token_to_data[token_id]["image_code"] = data["image_code"]
                token_to_data[token_id]["image_hash"] = image_code_to_hash[
                    data["image_code"]
                ]

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(SynchronizedData.token_to_data): token_to_data,
                    get_name(SynchronizedData.last_update_time): last_update_time
                }
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

    initial_round_cls: AppState = NewTokensRound
    initial_states: Set[AppState] = {NewTokensRound}
    transition_function: AbciAppTransitionFunction = {
        NewTokensRound: {
            Event.DONE: LeaderboardObservationRound,
            Event.CONTRACT_ERROR: NewTokensRound,
            Event.NO_MAJORITY: NewTokensRound,
            Event.ROUND_TIMEOUT: NewTokensRound,
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
    cross_period_persisted_keys: List[str] = [
        "token_to_data",
        "image_code_to_hash",
        "last_update_time",
    ]
