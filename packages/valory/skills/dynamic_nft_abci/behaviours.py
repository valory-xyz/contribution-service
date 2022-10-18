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

import json
from abc import abstractmethod
from typing import Generator, List, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.models import Params
from packages.valory.skills.dynamic_nft_abci.payloads import (
    LeaderboardObservationPayload,
    NewMembersPayload,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    DBUpdateRound,
    DynamicNFTAbciApp,
    ImageCodeCalculationRound,
    ImageGenerationRound,
    ImagePushRound,
    LeaderboardObservationRound,
    NewMembersRound,
    SynchronizedData,
)


BACKGROUND_THRESHOLDS = []
FRAME_THRESHOLDS = [1000, 2000, 3000]
BAR_THRESHOLDS = [200, 500]

IMAGE_URI_BASE = "https://pfp.autonolas.network/series/1/"

DUMMY_MEMBER_TO_NFT_URI = {
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A": f"{IMAGE_URI_BASE}/1",
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525": f"{IMAGE_URI_BASE}/2",
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7": f"{IMAGE_URI_BASE}/3",
    "0x19B043aD06C48aeCb2028B0f10503422BD0E0918": f"{IMAGE_URI_BASE}/4",
    "0x8325c5e4a56E352355c590E4A43420840F067F98": f"{IMAGE_URI_BASE}/5",  # this one does not appear in the leaderboard
}

DUMMY_LEADERBOARD = {
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A": 1500,
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525": 900,
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7": 575,
    "0x19B043aD06C48aeCb2028B0f10503422BD0E0918": 100,
    "0x7B394CD0B75f774c6808cc681b26aC3E5DF96E27": 3500,  # this one does not appear in the dummy members
}


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


class NewMembersBehaviour(DynamicNFTBaseBehaviour):
    """NewMemberListBehaviour"""

    behaviour_id: str = "new_member_list"
    matching_round: Type[AbstractRound] = NewMembersRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # Get a list of the new members
        # TODO: in the final implementation new members will be get from the contract
        old_members = set(self.synchronized_data.members.keys())
        member_to_uri = json.dumps(
            {k: v for k, v in DUMMY_MEMBER_TO_NFT_URI.items() if k not in old_members},
            sort_keys=True,
        )

        payload = NewMembersPayload(self.context.agent_address, member_to_uri)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()


class LeaderboardObservationBehaviour(DynamicNFTBaseBehaviour):
    """LeaderboardBehaviour"""

    behaviour_id: str = "leaderboard_observation"
    matching_round: Type[AbstractRound] = LeaderboardObservationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # Get the leaderboard
        # TODO: in the final implementation the leaderboard will be get from the API
        leaderboard = json.dumps(DUMMY_LEADERBOARD, sort_keys=True)
        payload = LeaderboardObservationPayload(self.context.agent_address, leaderboard)
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()


class ImageCodeCalculationBehaviour(DynamicNFTBaseBehaviour):
    """ImageCodeCalculationBehaviour"""

    behaviour_id: str = "image_code_calculation"
    matching_round: Type[AbstractRound] = ImageCodeCalculationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # for every entry in the leaderboard, agents look for members whose
        # number of points have changed with respect to the ones in the database
        # and will recalculate their images (but not store them yet)

    @staticmethod
    def get_layer_code(points: float, thresholds: List[int]) -> Tuple[str, float]:
        """Get the corresponding layer code.

        Layer codes have the format 00, 01, 02, 03...

        :param points: number of community points
        :param thresholds: layer thresholds that mark the points at which images change
        :returns: the layer code and the remainder points
        """
        for i, threshold in enumerate(thresholds):
            if points < threshold:
                prev_threshold = thresholds[i - 1] if i >= 1 else thresholds[0]
                return f"{i:02}", points - prev_threshold
        prev_threshold = thresholds[-1] if thresholds else 0
        return f"{len(thresholds):02}", points - prev_threshold

    @staticmethod
    def points_to_code(points: float) -> str:
        """Calculate the NFT image code given the number of community points

        :param points: number of community points
        :returns: the image code
        """

        if points < 0:
            raise ValueError("Points must be positive")

        # Points are updated after every call and we only keep the remainder
        bg_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, BACKGROUND_THRESHOLDS
        )
        fr_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, FRAME_THRESHOLDS
        )
        bar_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, BAR_THRESHOLDS
        )

        return bg_code + fr_code + bar_code


class ImageGenerationBehaviour(DynamicNFTBaseBehaviour):
    """ImageGenerationBehaviour"""

    behaviour_id: str = "image_generation"
    matching_round: Type[AbstractRound] = ImageGenerationRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # agents will check if the changes list contains an image code
        # that is not present on the redirect  table. This happens when
        # a member is granted a status whose corresponding image has never
        # been used. For each of these cases, agents will generate the new
        # images and get their corresponding IPFS hashes.


class ImagePushBehaviour(DynamicNFTBaseBehaviour):
    """ImagePushBehaviour"""

    behaviour_id: str = "image_push"
    matching_round: Type[AbstractRound] = ImagePushRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # every agent pushes the new images to IPFS. This is simpler as no
        # keepers are needed, does not affect the cost, introduces redundancy
        #  and the IPFS protocol will handle deduplication.


class DBUpdateBehaviour(DynamicNFTBaseBehaviour):
    """DBUpdateBehaviour"""

    behaviour_id: str = "db_update"
    matching_round: Type[AbstractRound] = DBUpdateRound

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        # Second table: the new image codes must be added with their uri (if applies).

        # First table: all entries whose points changed (the list from
        # ImageCodeCalculationRound) must now reflect the new points and (if it applies)
        # new image codes.

        # Third table: must be updated now to reflect the new redirects (if applies).


class DynamicNFTRoundBehaviour(AbstractRoundBehaviour):
    """DynamicNFTRoundBehaviour"""

    initial_behaviour_cls = NewMembersBehaviour
    abci_app_cls = DynamicNFTAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        NewMembersBehaviour,
        LeaderboardObservationBehaviour,
        ImageCodeCalculationBehaviour,
        ImageGenerationBehaviour,
        ImagePushBehaviour,
        DBUpdateBehaviour,
    ]
