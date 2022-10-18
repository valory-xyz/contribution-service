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

"""This module contains the transaction payloads of the DynamicNFTAbciApp."""

from enum import Enum
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    NEW_MEMBERS = "new_members"
    LEADERBOARD_OBSERVATION = "leaderboard_observation"
    IMAGE_CODE_CALCULATION = "image_code_calculation"
    IMAGE_GENERATION = "image_generation"
    IMAGE_PUSH = "image_push"
    DB_UPDATE = "db_update"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class NewMembersPayload(BaseTxPayload):
    """Represent a transaction payload for the NewMembersRound."""

    transaction_type = TransactionType.NEW_MEMBERS

    def __init__(self, sender: str, member_to_uri: str, **kwargs: Any) -> None:
        """Initialize an 'new_members' transaction payload.

        :param sender: the sender (Ethereum) address
        :param member_to_uri: a member to uri dict json encoded
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._member_to_uri = member_to_uri

    @property
    def member_to_uri(self) -> str:
        """Get the member_to_uri."""
        return self._member_to_uri

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(member_to_uri=self.member_to_uri)


class LeaderboardObservationPayload(BaseTxPayload):
    """Represent a transaction payload for the LeaderboardObservationRound."""

    transaction_type = TransactionType.LEADERBOARD_OBSERVATION

    def __init__(self, sender: str, leaderboard: str, **kwargs: Any) -> None:
        """Initialize an 'leaderboard_observation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param leaderboard: the leaderboard json encoded
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._leaderboard = leaderboard

    @property
    def leaderboard(self) -> str:
        """Get the leaderboard."""
        return self._leaderboard

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(leaderboard=self.leaderboard)


class ImageCodeCalculationPayload(BaseTxPayload):
    """Represent a transaction payload for the ImageCodeCalculationRound."""

    transaction_type = TransactionType.IMAGE_CODE_CALCULATION


class ImageGenerationPayload(BaseTxPayload):
    """Represent a transaction payload for the ImageGenerationRound."""

    transaction_type = TransactionType.IMAGE_GENERATION


class ImagePushPayload(BaseTxPayload):
    """Represent a transaction payload for the ImagePushRound."""

    transaction_type = TransactionType.IMAGE_PUSH


class DBUpdatePayload(BaseTxPayload):
    """Represent a transaction payload for the DBUpdateRound."""

    transaction_type = TransactionType.DB_UPDATE
