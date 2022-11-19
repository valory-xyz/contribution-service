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
import shutil
from logging import Logger
from pathlib import Path
from typing import Any, Generator, List, Optional, Set, Tuple, Type, cast

from PIL import Image
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.ipfs.base import IPFSHashOnly

from packages.valory.contracts.ERC721Collective.contract import ERC721CollectiveContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.io_.load import Loader
from packages.valory.skills.dynamic_nft_abci.io_.store import (
    ExtendedSupportedFiletype,
    Storer,
)
from packages.valory.skills.dynamic_nft_abci.models import Params
from packages.valory.skills.dynamic_nft_abci.payloads import (
    DBUpdatePayload,
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


NULL_ADDRESS = "0x0000000000000000000000000000000000000000"


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
        """Get a list of the new members."""
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():

            member_to_token_id = yield from self.get_member_to_token_id()

            if member_to_token_id == NewMembersRound.ERROR_PAYLOAD:
                new_member_to_uri = json.dumps(
                    NewMembersRound.ERROR_PAYLOAD, sort_keys=True
                )
            else:
                member_to_nft_uri = {
                    member: f"{self.params.token_uri_base}/{token_id}"
                    for member, token_id in member_to_token_id.items()
                }
                old_members = set(self.synchronized_data.members.keys())
                new_member_to_uri = json.dumps(
                    {
                        member: {"uri": uri, "points": None, "image_code": None}
                        for member, uri in member_to_nft_uri.items()
                        if member not in old_members
                    },
                    sort_keys=True,
                )
                self.context.logger.info(
                    f"Got the new member list: {new_member_to_uri}"
                )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = NewMembersPayload(self.context.agent_address, new_member_to_uri)
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_member_to_token_id(self) -> Generator[None, None, dict]:
        """Get member to token id data."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.params.syndicate_contract_address,
            contract_id=str(ERC721CollectiveContract.contract_id),
            contract_callable="get_all_erc721_transfers",
            from_address=NULL_ADDRESS,
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.info("Error retrieving the member to token_id data")
            return NewMembersRound.ERROR_PAYLOAD
        data = cast(dict, contract_api_msg.state.body["member_to_token_id"])
        self.context.logger.info(f"Got member to token_id data: {data}")
        return data


class LeaderboardObservationBehaviour(DynamicNFTBaseBehaviour):
    """LeaderboardBehaviour"""

    behaviour_id: str = "leaderboard_observation"
    matching_round: Type[AbstractRound] = LeaderboardObservationRound

    def async_act(self) -> Generator:
        """Get the leaderboard."""
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():
            data = yield from self.get_data()
            self.context.logger.info(f"Received points from Leaderboard API: {data}")

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = LeaderboardObservationPayload(self.context.agent_address, data)
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_data(self) -> Generator[None, None, str]:
        """
        Get the data from the Leaderboard API.

        :yield: HttpMessage object
        :return: return the data retrieved from the Leaderboard API, in case something goes wrong we return "{}".
        """
        leaderboard_endpoint = self.params.leaderboard_endpoint

        # While running e2e tests, the mock api server does not work
        # if parameters are sent in the url, ao we remove them here.
        if "mock_sheet_id" in leaderboard_endpoint:
            leaderboard_endpoint = leaderboard_endpoint.split("?")[0]

        self.context.logger.info(
            f"Sending leaderboard request to: {leaderboard_endpoint}"
        )
        response = yield from self.get_http_response(
            method="GET",
            url=leaderboard_endpoint,
        )
        if response.status_code != 200:
            self.context.logger.error(
                f"Could not retrieve data from the Leaderboard API. "
                f"Received status code {response.status_code}."
            )
            return "{}"

        try:
            # Parse the response bytes into a dict
            response_json = json.loads(response.body)

            # We retrieve both leaderboard and layer data in the same call
            # so we need to iterate it and identify each one by its "valueRanges" field
            response_body = {}
            for data in response_json["valueRanges"]:
                if data["range"] == self.params.leaderboard_points_range:
                    leaderboard_raw = data["values"]

                    # Format the leaderboard: build a dictionary like the following
                    # leaderboard = {       # noqa: E800
                    #    "wallet_0": 1000,  # noqa: E800
                    #    "wallet_1": 1500,  # noqa: E800
                    #     ...
                    # }                     # noqa: E800
                    leaderboard = {
                        entry[0]: int(entry[1])
                        for entry in leaderboard_raw
                        if LedgerApis.is_valid_address(DEFAULT_LEDGER, entry[0])
                    }

                    if len(leaderboard) != len(leaderboard_raw):
                        self.context.logger.error(
                            "Some elements in the leaderboard are not valid and have been skipped."
                        )

                    response_body["leaderboard"] = leaderboard
                    continue

                if data["range"] == self.params.leaderboard_layers_range:
                    layers_raw = data["values"]

                    layer_names = ImageGenerationBehaviour.ImageManager.LAYER_NAMES

                    # Format the layers: build a dictionary like the following:
                    # layers = {                                               # noqa: E800
                    #   "classes": {0: "hash", 1000: "hash", ...},  # layer 0  # noqa: E800
                    #   "frames": {0: "hash", 1000: "hash", ...},   # layer 1  # noqa: E800
                    #   ...
                    # }                                                        # noqa: E800
                    layers = {layer_name: {} for layer_name in layer_names}
                    for layer_index, layer_data in enumerate(layers_raw):
                        for image_data in layer_data:
                            points, image_hash = image_data.split(":")
                            layers[layer_names[layer_index]][int(points)] = image_hash

                    response_body["layers"] = layers

        except (KeyError, ValueError, TypeError) as e:
            self.context.logger.error(
                f"Could not parse response from the Leaderboard API, "
                f"the following error was encountered {type(e).__name__}: {e}"
            )
            return "{}"

        except Exception as e:  # pylint: disable=broad-except
            self.context.logger.error(
                f"An unexpected error was encountered while parsing the Leaderboard response "
                f"{type(e).__name__}: {e}"
            )
            return "{}"

        # We dump the json into a string, notice the sort_keys=True.
        # We MUST ensure that they keys are ordered in the same way,
        # otherwise the payload MAY end up being different on different
        # agents. This can happen in case the API responds with keys
        # in different order, which can happen since there is no requirement
        # against this.
        deterministic_body = json.dumps(response_body, sort_keys=True)
        return deterministic_body

    @staticmethod
    def validate_api_data(data):
        """Fixes format problems derived from serialization and de-serialization.

        :param data: the source data
        :returns: the fixed data
        """

        fixed_layer_data = {}
        for layer_name, layer_data in data["layers"].items():
            fixed_layer_data[layer_name] = {}
            for threshold, hash_ in layer_data.items():
                # Integer keys must be int, not str
                fixed_layer_data[layer_name][int(threshold)] = hash_

        data["layers"] = fixed_layer_data

        return data


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
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():
            api_data = LeaderboardObservationBehaviour.validate_api_data(
                self.synchronized_data.most_voted_api_data
            )
            leaderboard = api_data["leaderboard"]
            layer_data = api_data["layers"]
            thresholds = {k: list(v.keys()) for k, v in layer_data.items()}
            members = self.synchronized_data.members

            member_updates = {}
            for member, new_points in leaderboard.items():
                if member not in members or members[member]["points"] != new_points:
                    self.context.logger.info(
                        f"Calculating image code for member {member}: points={new_points} thresholds={thresholds}"
                    )
                    image_code = self.points_to_code(new_points, thresholds)
                    member_updates[member] = {
                        "points": new_points,
                        "image_code": image_code,
                    }
                    self.context.logger.info(
                        f"Image code for member {member} is {image_code}"
                    )

            member_updates_serialized = json.dumps(member_updates, sort_keys=True)
            self.context.logger.info(
                f"Calculated member updates: {member_updates_serialized}"
            )

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
        if len(thresholds) < 1:
            raise ValueError(
                f"Threshold list must contain at least one value: {thresholds}"
            )

        if points < thresholds[0]:
            raise ValueError(
                f"Points for this layer must be greater than {thresholds[0]}, got {points}"
            )

        code = None
        remaining_points = None

        for i, threshold in enumerate(thresholds):
            if points >= threshold:
                code = i
                remaining_points = points - threshold
            else:
                break

        return f"{code:02}", remaining_points

    @staticmethod
    def points_to_code(points: float, thresholds: dict) -> str:
        """Calculate the NFT image code given the number of community points.

        Examples of image codes: 000001, 010300, 020102....

        :param points: number of community points
        :param thresholds: thresholds dict
        :returns: the image code
        """

        if points < 0:
            raise ValueError("Points must be positive")

        # Points are updated after every call and we only keep the remainder
        cls_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, thresholds[ImageGenerationBehaviour.ImageManager.LAYER_NAMES[0]]
        )
        fr_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, thresholds[ImageGenerationBehaviour.ImageManager.LAYER_NAMES[1]]
        )
        bar_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, thresholds[ImageGenerationBehaviour.ImageManager.LAYER_NAMES[2]]
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
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():
            # Get new layers from IPFS if needed
            self.update_layers()

            # In the current implementation, the image manager will be instanced every time the behaviour is run.
            # This is not ideal: a singleton or another pattern that avoids this might be more suited to our usecase.
            img_manager = self.ImageManager(logger=self.context.logger)

            # Get the image codes that have been never generated
            new_image_code_to_images = {}
            for update in self.synchronized_data.most_voted_member_updates.values():
                if update["image_code"] not in self.synchronized_data.images:
                    self.context.logger.info(
                        f"Image {update['image_code']} does not exist. Generating..."
                    )
                    new_image_code_to_images[
                        update["image_code"]
                    ] = img_manager.generate(update["image_code"])

            if None in new_image_code_to_images.values():
                self.context.logger.info(
                    "An error happened while generating the new images"
                )
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
                    # Whitelist the image
                    self.context.logger.info(
                        f"Getting hash for image at {image_path}..."
                    )
                    image_hash = IPFSHashOnly.get(str(image_path))
                    self.context.logger.info(
                        f"Hash is for {image_path} is {image_hash}. Trying to whitelist..."
                    )
                    whitelist_success = yield from self.whitelist_hash(image_hash)
                    if not whitelist_success:
                        self.context.logger.info(
                            f"Error whitelisting image with hash {image_hash}"
                        )
                        status = "error"
                        break

                    self.context.logger.info(
                        f"Image with hash {image_hash} was whitelisted"
                    )

                    # Send
                    self.context.logger.info(
                        f"Trying to whitelist image with hash {image_hash}..."
                    )
                    image_hash = self.send_to_ipfs(
                        image_path, image, filetype=ExtendedSupportedFiletype.PNG
                    )

                    if not image_hash:
                        self.context.logger.info(
                            f"Error pushing image with hash {image_hash} to IPFS"
                        )
                        status = "error"
                        break

                    self.context.logger.info(
                        f"Image with hash {image_hash} was pushed to IPFS"
                    )

                    new_image_code_to_hashes[image_code] = image_hash

            self.context.logger.info(
                f"Generated the following new images: {new_image_code_to_hashes}"
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

    def update_layers(self):
        """Updates local layer if they dont match the ones from the leaderboard API"""
        api_data = LeaderboardObservationBehaviour.validate_api_data(
            self.synchronized_data.most_voted_api_data
        )
        api_layer_data = api_data["layers"]

        for layer_name in self.ImageManager.LAYER_NAMES:

            api_layer_hashes = set(api_layer_data[layer_name].values())

            layer_path = Path(
                self.ImageManager.IMAGE_ROOT, self.ImageManager.LAYERS_DIR, layer_name
            )

            self.context.logger.info(f"Checking local image hashes from: {layer_path}")

            local_layer_hashes = set(
                IPFSHashOnly.get(image_file)
                for image_file in layer_path.rglob(f"*.{self.ImageManager.PNG_EXT}")
            )

            # Check if some image has changed and re-download images
            if api_layer_hashes != local_layer_hashes:
                self.context.logger.info(
                    f"Layer '{layer_name}' is out of date. Local={local_layer_hashes}, API={api_layer_hashes} Re-downloading."
                )
                # Remove local images
                if os.path.isdir(layer_path):
                    shutil.rmtree(layer_path)
                os.makedirs(layer_path)

                # Get new images from IPFS. They are stored in alphabetical order.
                for i, image_hash in enumerate(api_layer_hashes):
                    self.get_from_ipfs(
                        hash_=image_hash,
                        target_dir=layer_path,
                        multiple=False,
                        filename=str(i),
                        filetype=ExtendedSupportedFiletype.PNG,
                    )
            else:
                self.context.logger.info(f"Layer {layer_name} is already up to date")

    def whitelist_hash(self, image_hash: str) -> Generator[None, None, bool]:
        """Send a whitelist request to the whitelist server

        :param image_hash: the hash to whitelist
        :returns: True on success, False on error
        """
        response = yield from self.get_http_response(
            method="POST",
            url=f"{self.params.whitelist_endpoint}",
            content=json.dumps(
                {"hash": image_hash, "key": self.params.whitelist_api_key}
            ).encode(),
        )
        if response.status_code != 200:
            self.context.logger.error(
                f"Could not whitelist the hash {image_hash}. "
                f"Received status code {response.status_code} "
                f"from {self.params.whitelist_endpoint}"
            )
            return False

        return True

    class ImageManager:
        """Class to load image layers and compose new images from them"""

        IMAGE_ROOT = Path(Path(__file__).parent, "data")
        LAYERS_DIR = "layers"
        IMAGES_DIR = "images"
        LAYER_NAMES = ("classes", "frames", "bars")
        PNG_EXT = "png"
        CODE_LEN = 6

        def __init__(self, logger: Logger, image_root: Path = IMAGE_ROOT):
            """Load images"""
            self.logger = logger
            self.image_root = image_root
            self.layers = self._load_layers()

            self.logger.info(f"ImageManager: loaded layer images: {self.layers}")

            # Create the output directory if it does not exist
            self.out_path = Path(self.image_root, self.IMAGES_DIR)
            os.makedirs(self.out_path, exist_ok=True)

        def _load_layers(self) -> tuple:
            """Get the available images for each layer, sorted by name"""
            return tuple(
                tuple(
                    sorted(
                        Path(self.image_root, self.LAYERS_DIR, i).rglob(
                            f"*.{self.PNG_EXT}"
                        )
                    )
                    for i in self.LAYER_NAMES
                )
            )

        def generate(self, image_code: str) -> Optional[Image.Image]:
            """Generate an image"""

            # Check code length
            if len(image_code) != self.CODE_LEN:
                self.logger.error(
                    f"ImageManager: invalid code '{image_code}'. Length is {len(image_code)}, should be {self.CODE_LEN}."
                )
                return None

            img_layer_codes = [int(image_code[i : i + 2]) for i in range(0, 6, 2)]

            # Check that code indices do not reference non-existent images
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

            # Save image
            img_path = Path(self.out_path, f"{image_code}.{self.PNG_EXT}")
            img_layers[0].save(str(img_path))
            self.logger.info(
                f"Image {image_code} has been generated and saved at {img_path}"
            )

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
        self.context.logger.info(
            "Updating database tables",
        )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = DBUpdatePayload(
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
