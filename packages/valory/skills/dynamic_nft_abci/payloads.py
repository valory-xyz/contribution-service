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
from typing import Any, Dict, Hashable, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    # TODO: define transaction types: e.g. TX_HASH: "tx_hash"
    D_B_UPDATE = "d_b_update"
    IMAGE_CODE_CALCULATION = "image_code_calculation"
    IMAGE_GENERATION = "image_generation"
    IMAGE_PUSH = "image_push"
    NEW_MEMBER_LIST = "new_member_list"
    NEW_MEMBER_UPDATE = "new_member_update"
    OBSERVATION = "observation"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseDynamicNFTPayload(BaseTxPayload, ABC):
    """Base payload for DynamicNFT."""

    def __init__(self, sender: str, content: Hashable, **kwargs: Any) -> None:
        """Initialize a 'select_keeper' transaction payload."""

        super().__init__(sender, **kwargs)
        setattr(self, f"_{self.transaction_type}", content)
        p = property(lambda s: getattr(self, f"_{self.transaction_type}"))
        setattr(self.__class__, f"{self.transaction_type}", p)

    @property
    def data(self) -> Dict[str, Hashable]:
        """Get the data."""
        return {str(self.transaction_type): getattr(self, str(self.transaction_type))}


class DBUpdatePayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the DBUpdateRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.D_B_UPDATE


class ImageCodeCalculationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImageCodeCalculationRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.IMAGE_CODE_CALCULATION


class ImageGenerationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImageGenerationRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.IMAGE_GENERATION


class ImagePushPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ImagePushRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.IMAGE_PUSH


class NewMemberListPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the NewMemberListRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.NEW_MEMBER_LIST


class NewMemberUpdatePayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the NewMemberUpdateRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.NEW_MEMBER_UPDATE


class ObservationPayload(BaseDynamicNFTPayload):
    """Represent a transaction payload for the ObservationRound."""

    # TODO: specify the transaction type
    transaction_type = TransactionType.OBSERVATION

