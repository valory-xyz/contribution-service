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
import os
from logging import Logger
from pathlib import Path
from typing import Any, Generator, List, Optional, Set, Tuple, Type, cast

from PIL import Image

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.io_.load import Loader
from packages.valory.skills.dynamic_nft_abci.io_.store import Storer
from packages.valory.skills.dynamic_nft_abci.models import Params
from packages.valory.skills.dynamic_nft_abci.payloads import (
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    LeaderboardObservationPayload,
    NewMembersPayload,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    DBUpdateRound,
    DynamicNFTAbciApp,
    ImageCodeCalculationRound,
    ImageGenerationRound,
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

IMAGE_ROOT = Path("tmp")


class DynamicNFTBaseBehaviour(BaseBehaviour):
    """Base behaviour for the common apps' skill."""

    def __init__(self, **kwargs: Any):
        """Initialize a Dynamic NFT base behaviour."""
        super().__init__(**kwargs, loader_cls=Loader, storer_cls=Storer)

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

    behaviour_id: str = "new_members"
    matching_round: Type[AbstractRound] = NewMembersRound

    def async_act(self) -> Generator:
        """Get a list of the new members.

        TODO: in the final implementation new members will be get from the contract.
        """
        old_members = set(self.synchronized_data.members.keys())
        new_member_to_uri = json.dumps(
            {
                member: {"uri": uri, "points": None, "image_code": None}
                for member, uri in DUMMY_MEMBER_TO_NFT_URI.items()
                if member not in old_members
            },
            sort_keys=True,
        )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = NewMembersPayload(self.context.agent_address, new_member_to_uri)
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class LeaderboardObservationBehaviour(DynamicNFTBaseBehaviour):
    """LeaderboardBehaviour"""

    behaviour_id: str = "leaderboard_observation"
    matching_round: Type[AbstractRound] = LeaderboardObservationRound

    def async_act(self) -> Generator:
        """Get the leaderboard.

        TODO: in the final implementation the leaderboard will be get from the API
        """
        leaderboard = json.dumps(DUMMY_LEADERBOARD, sort_keys=True)

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = LeaderboardObservationPayload(
                self.context.agent_address, leaderboard
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ImageCodeCalculationBehaviour(DynamicNFTBaseBehaviour):
    """ImageCodeCalculationBehaviour"""

    behaviour_id: str = "image_code_calculation"
    matching_round: Type[AbstractRound] = ImageCodeCalculationRound

    def async_act(self) -> Generator:
        """
        Calculate the image codes.

        For every entry in the leaderboard, agents look for members whose
        number of points have changed with respect to the ones in the database
        and will recalculate their images (but not store them yet).
        """
        leaderboard = self.synchronized_data.most_voted_leaderboard
        members = self.synchronized_data.members

        member_updates = {}
        for member, new_points in leaderboard.items():
            if member not in members or members[member]["points"] != new_points:
                image_code = self.points_to_code(new_points)
                member_updates[member] = {
                    "points": new_points,
                    "image_code": image_code,
                }

        member_updates_serialized = json.dumps(member_updates, sort_keys=True)

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = ImageCodeCalculationPayload(
                self.context.agent_address, member_updates_serialized
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

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
        """Calculate the NFT image code given the number of community points.

        Examples of image codes: 000001, 010300, 020102....

        :param points: number of community points
        :returns: the image code
        """

        if points < 0:
            raise ValueError("Points must be positive")

        # Points are updated after every call and we only keep the remainder
        cls_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, BACKGROUND_THRESHOLDS
        )
        fr_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, FRAME_THRESHOLDS
        )
        bar_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, BAR_THRESHOLDS
        )

        return cls_code + fr_code + bar_code


class ImageGenerationBehaviour(DynamicNFTBaseBehaviour):
    """ImageGenerationBehaviour"""

    behaviour_id: str = "image_generation"
    matching_round: Type[AbstractRound] = ImageGenerationRound

    def async_act(self) -> Generator:
        """Generate the images.

        Check if the changes list contains an image code
        that is not present in the redirect  table. This happens when
        a member is granted a status whose corresponding image has never
        been used. For each of these cases, agents generate the new
        images and push them to IPFS.
        """

        # In the current implementation, the image manager will be instanced every time the behaviour is run.
        # This is not ideal: a singleton or another pattern that avoids this might be more suited to our usecase.
        img_manager = self.ImageManager(logger=self.context.logger)

        # Get the image codes that have been never generated
        new_image_code_to_images = {}
        for update in self.synchronized_data.most_voted_member_updates.values():
            if update["image_code"] not in self.synchronized_data.images:
                new_image_code_to_images[update["image_code"]] = img_manager.generate(
                    update["image_code"]
                )

        if None in new_image_code_to_images.values():
            status = "error"
            new_image_code_to_hashes = {}
        else:
            status = "success"
            # Push to IPFS
            new_image_code_to_hashes = {}
            for image_code, image in new_image_code_to_images.items():
                image_path = Path(
                    img_manager.out_path, f"{image_code}.{img_manager.PNG_EXT}"
                )
                new_image_code_to_hashes[image_code] = self.send_to_ipfs(
                    image_path, image
                )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = ImageGenerationPayload(
                self.context.agent_address,
                json.dumps(
                    {
                        "status": status,
                        "new_image_code_to_hashes": new_image_code_to_hashes,
                    },
                    sort_keys=True,
                ),
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    class ImageManager:
        """Class to load image layers and compose new images from them"""

        LAYERS_DIR = "layers"
        IMAGES_DIR = "images"
        CLASSES = "classes"
        FRAMES = "frames"
        BARS = "bars"
        PNG_EXT = "png"
        CODE_LEN = 6

        def __init__(self, logger: Logger, image_root: Path = IMAGE_ROOT):
            """Load images"""
            self.logger = logger
            self.image_root = image_root
            self.layers = (  # lists of available images for each layer, sorted by name
                tuple(
                    tuple(
                        sorted(
                            Path(image_root, self.LAYERS_DIR, i).rglob(
                                f"*.{self.PNG_EXT}"
                            )
                        )
                    )
                    for i in (self.CLASSES, self.FRAMES, self.BARS)
                )
            )

            # Create the output directory if it does not exist
            self.out_path = Path(self.image_root, self.IMAGES_DIR)
            os.makedirs(self.out_path, exist_ok=True)

        def generate(self, image_code: str) -> Optional[Image.Image]:
            """Generate an image"""

            # Check code validity
            if len(image_code) != self.CODE_LEN:
                self.logger.error(
                    f"ImageManager: invalid code '{image_code}'. Length is {len(image_code)}, should be {self.CODE_LEN}."
                )
                return None

            img_layer_codes = [int(image_code[i : i + 2]) for i in range(0, 6, 2)]

            for layer_index, layer_code in enumerate(img_layer_codes):
                if layer_code >= len(self.layers[layer_index]):
                    self.logger.error(
                        f"ImageManager: invalid code '{image_code}'. Layer {layer_index} code must be lower than {len(self.layers[layer_index])}. Found {layer_code}."
                    )
                    return None

            # Get layers
            img_layers = [
                Image.open(str(self.layers[layer_index][layer_code]))
                for layer_index, layer_code in enumerate(img_layer_codes)
            ]

            # Combine layers
            img_layers[0].paste(img_layers[1], (0, 0), mask=img_layers[1])
            img_layers[0].paste(img_layers[2], (0, 0), mask=img_layers[2])
            return img_layers[0]


class DBUpdateBehaviour(DynamicNFTBaseBehaviour):
    """DBUpdateBehaviour"""

    behaviour_id: str = "db_update"
    matching_round: Type[AbstractRound] = DBUpdateRound

    def async_act(self) -> Generator:
        """Update the database tables.

        User table: all entries whose points changed (the list from
        ImageCodeCalculationRound) must now reflect the new points and (if it applies)
        new image codes.

        Redirect table: must be updated now to reflect the new redirects (if it applies).
        """
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = ImageGenerationPayload(
                self.context.agent_address,
                json.dumps(
                    {},  # empty payload for now
                    sort_keys=True,
                ),
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class DynamicNFTRoundBehaviour(AbstractRoundBehaviour):
    """DynamicNFTRoundBehaviour"""

    initial_behaviour_cls = NewMembersBehaviour
    abci_app_cls = DynamicNFTAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        NewMembersBehaviour,
        LeaderboardObservationBehaviour,
        ImageCodeCalculationBehaviour,
        ImageGenerationBehaviour,
        DBUpdateBehaviour,
    ]
