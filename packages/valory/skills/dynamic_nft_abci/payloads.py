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

from abc import ABC
from enum import Enum
from typing import Any, Dict, Hashable

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


class BaseDynamicNFTPayload(BaseTxPayload, ABC):
    """Base payload for DynamicNFT."""

    def __init__(self, sender: str, content: Hashable, **kwargs: Any) -> None:
        """Initialize a transaction payload."""
        super().__init__(sender, **kwargs)
        self._content = content

    @property
    def content(self):
        """Get the content."""
        return self._content

    @property
    def data(self) -> Dict[str, Hashable]:
        """Get the data."""
        return dict(content=self.content)


class NewMembersPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the NewMembersRound."""

    transaction_type = TransactionType.NEW_MEMBERS


class LeaderboardObservationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the LeaderboardObservationRound."""

    transaction_type = TransactionType.LEADERBOARD_OBSERVATION


class ImageCodeCalculationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImageCodeCalculationRound."""

    transaction_type = TransactionType.IMAGE_CODE_CALCULATION


class ImageGenerationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImageGenerationRound."""

    transaction_type = TransactionType.IMAGE_GENERATION


class ImagePushPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImagePushRound."""

    transaction_type = TransactionType.IMAGE_PUSH


class DBUpdatePayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the DBUpdateRound."""

    transaction_type = TransactionType.DB_UPDATE
