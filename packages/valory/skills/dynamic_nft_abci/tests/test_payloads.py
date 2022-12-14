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

"""This package contains payload tests for the DynamicNFTAbciApp."""

from dataclasses import dataclass
from typing import Hashable

import pytest

from packages.valory.skills.dynamic_nft_abci.payloads import (
    BaseDynamicNFTPayload,
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    LeaderboardObservationPayload,
    NewTokensPayload,
    TransactionType,
)


@dataclass
class PayloadTestCase:
    """PayloadTestCase"""

    payload_cls: BaseDynamicNFTPayload
    content: Hashable
    transaction_type: TransactionType


@pytest.mark.parametrize(
    "test_case",
    [
        PayloadTestCase(
            payload_cls=NewTokensPayload,
            content="payload_test_content",
            transaction_type=TransactionType.NEW_TOKENS,
        ),
        PayloadTestCase(
            payload_cls=LeaderboardObservationPayload,
            content="payload_test_content",
            transaction_type=TransactionType.LEADERBOARD_OBSERVATION,
        ),
        PayloadTestCase(
            payload_cls=ImageCodeCalculationPayload,
            content="payload_test_content",
            transaction_type=TransactionType.IMAGE_CODE_CALCULATION,
        ),
        PayloadTestCase(
            payload_cls=ImageGenerationPayload,
            content="payload_test_content",
            transaction_type=TransactionType.IMAGE_GENERATION,
        ),
        PayloadTestCase(
            payload_cls=DBUpdatePayload,
            content="payload_test_content",
            transaction_type=TransactionType.DB_UPDATE,
        ),
    ],
)
def test_payloads(test_case: PayloadTestCase) -> None:
    """Tests for DynamicNFTAbciApp payloads"""

    payload = test_case.payload_cls(sender="sender", content=test_case.content)
    assert payload.sender == "sender"
    assert payload.content == test_case.content
    assert payload.transaction_type == test_case.transaction_type
    assert payload.from_json(payload.json) == payload
