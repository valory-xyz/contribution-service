# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

from dataclasses import dataclass

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class NewTokensPayload(BaseTxPayload):
    """Represent a transaction payload for the NewTokensRound."""

    content: str


@dataclass(frozen=True)
class LeaderboardObservationPayload(BaseTxPayload):
    """Represent a transaction payload for the LeaderboardObservationRound."""

    content: str


@dataclass(frozen=True)
class ImageCodeCalculationPayload(BaseTxPayload):
    """Represent a transaction payload for the ImageCodeCalculationRound."""

    content: str


@dataclass(frozen=True)
class ImageGenerationPayload(BaseTxPayload):
    """Represent a transaction payload for the ImageGenerationRound."""

    content: str


@dataclass(frozen=True)
class DBUpdatePayload(BaseTxPayload):
    """Represent a transaction payload for the DBUpdateRound."""

    content: str
