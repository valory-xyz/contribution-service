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
from valory.skills.dynamic_nft_abci.payloads import (
    BaseDynamicNFTPayload,
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    ImagePushPayload,
    NewMemberListPayload,
    NewMemberUpdatePayload,
    ObservationPayload,
    TransactionType,
)


@dataclass
class PayloadTestCase:
    """PayloadTestCase"""

    payload_cls: BaseDynamicNFTPayload
    content: Hashable
    transaction_type: TransactionType


# TODO: provide test cases
@pytest.mark.parametrize("test_case", [])
def test_payloads(test_case: PayloadTestCase) -> None:
    """Tests for DynamicNFTAbciApp payloads"""

    payload = test_case.payload_cls(sender="sender", content=test_case.content)
    assert payload.sender == "sender"
    assert getattr(payload, f"{payload.transaction_type}") == test_case.content
    assert payload.transaction_type == test_case.transaction_type
    assert payload.from_json(payload.json) == payload
