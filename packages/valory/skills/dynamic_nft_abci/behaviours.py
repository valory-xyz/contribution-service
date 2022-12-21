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
import re
import shutil
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Type, cast
from urllib.parse import urlparse

import jsonschema
from PIL import Image
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.base import IPFS_HASH_REGEX
from aea.helpers.ipfs.base import IPFSHashOnly

from packages.valory.contracts.dynamic_contribution.contract import (
    DynamicContributionContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviour_utils import TimeoutException
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.io_.load import Loader
from packages.valory.skills.dynamic_nft_abci.io_.store import (
    ExtendedSupportedFiletype,
    Storer,
)
from packages.valory.skills.dynamic_nft_abci.models import Params, SharedState
from packages.valory.skills.dynamic_nft_abci.payloads import (
    DBUpdatePayload,
    ImageCodeCalculationPayload,
    ImageGenerationPayload,
    LeaderboardObservationPayload,
    NewTokensPayload,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    DBUpdateRound,
    DynamicNFTAbciApp,
    ImageCodeCalculationRound,
    ImageGenerationRound,
    LeaderboardObservationRound,
    NewTokensRound,
    SynchronizedData,
)
from packages.valory.skills.dynamic_nft_abci.tools import SHEET_API_SCHEMA


NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
HTTP_TIMEOUT = 10
DEFAULT_POINTS = 0
DEFAULT_IMAGE_CODE = "000000"
THRESHOLD_REGEX = rf"^\d+:{IPFS_HASH_REGEX}$"


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


class NewTokensBehaviour(DynamicNFTBaseBehaviour):
    """NewTokensBehaviour"""

    matching_round: Type[AbstractRound] = NewTokensRound

    def async_act(self) -> Generator:
        """Get a list of the new tokens."""
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():

            token_id_to_address = yield from self.get_token_id_to_member()

            if token_id_to_address == NewTokensRound.ERROR_PAYLOAD:
                payload_data = json.dumps(NewTokensRound.ERROR_PAYLOAD, sort_keys=True)
            else:
                old_tokens = set(self.synchronized_data.token_to_data.keys())

                # Add new tokens only
                new_token_to_data = {
                    token_id: {
                        "address": address,
                        "points": DEFAULT_POINTS,
                        "image_code": DEFAULT_IMAGE_CODE,
                        "image_hash": self.context.params.basic_image_cid,
                    }
                    for token_id, address in token_id_to_address.items()
                    if token_id not in old_tokens
                }
                self.context.logger.info(f"Got the new token list: {new_token_to_data}")

                payload_data = json.dumps(
                    {
                        "new_token_to_data": new_token_to_data,
                    },
                    sort_keys=True,
                )

                self.context.logger.info(f"Payload data={payload_data}")

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = NewTokensPayload(self.context.agent_address, payload_data)
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_token_id_to_member(self) -> Generator[None, None, dict]:
        """Get token id to member data."""
        self.context.logger.info(
            f"Retrieving Transfer events later than block {self.params.earliest_block_to_monitor}"
            f" for contract at {self.params.dynamic_contribution_contract_address}"
        )
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.params.dynamic_contribution_contract_address,
            contract_id=str(DynamicContributionContract.contract_id),
            contract_callable="get_all_erc721_transfers",
            from_address=NULL_ADDRESS,
            from_block=self.params.earliest_block_to_monitor,
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.info("Error retrieving the token_id to member data")
            return NewTokensRound.ERROR_PAYLOAD
        data = cast(dict, contract_api_msg.state.body["token_id_to_member"])
        self.context.logger.info(f"Got token_id to member data: {data}")
        return data


class LeaderboardObservationBehaviour(DynamicNFTBaseBehaviour):
    """LeaderboardBehaviour"""

    matching_round: Type[AbstractRound] = LeaderboardObservationRound

    def async_act(self) -> Generator:
        """Get the leaderboard."""
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():
            data = yield from self.get_data()
            self.context.logger.info(f"Received points from Leaderboard API: {data}")

            # We dump the json into a string, notice the sort_keys=True.
            # We MUST ensure that they keys are ordered in the same way,
            # otherwise the payload MAY end up being different on different
            # agents. This can happen in case the API responds with keys
            # in different order, which can happen since there is no requirement
            # against this.
            deterministic_body = json.dumps(data, sort_keys=True)

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = LeaderboardObservationPayload(
                self.context.agent_address, deterministic_body
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_data(self) -> Generator[None, None, Dict]:
        """
        Get the data from the Leaderboard API.

        :yield: HttpMessage object
        :return: return the data retrieved from the Leaderboard API, in case something goes wrong we return "{}".
        """
        leaderboard_endpoint = self.params.leaderboard_endpoint

        # While running e2e tests, the mock api server does not work
        # if parameters are sent in the url, so we remove them here.
        if "mock_sheet_id" in leaderboard_endpoint:
            parsed_endpoint = urlparse(leaderboard_endpoint)
            leaderboard_endpoint = "{uri.scheme}://{uri.netloc}{uri.path}".format(
                uri=parsed_endpoint
            )

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
            return LeaderboardObservationRound.ERROR_PAYLOAD

        try:
            # Parse the response bytes into a dict
            response_json = json.loads(response.body)

            if not self.validate_api_data(response_json):
                self.context.logger.error(f"API data is not valid:\n{response_json}")
                return LeaderboardObservationRound.ERROR_PAYLOAD

            # We retrieve both leaderboard and layer data in the same call
            # so we need to iterate it and identify each one by its "valueRanges" field
            response_body = {}

            for data in response_json["valueRanges"]:

                # Score data
                if data["range"] == self.params.leaderboard_points_range:
                    leaderboard_raw = data["values"]

                    # Format the leaderboard: build a dictionary like the following
                    # leaderboard = {       # noqa: E800
                    #    "wallet_0": 1000,  # noqa: E800
                    #    "wallet_1": 1500,  # noqa: E800
                    #     ...
                    # }                     # noqa: E800
                    # Non valid addresses are skipped
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

                # Layers data
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

        except Exception as e:  # pylint: disable=broad-except
            self.context.logger.error(
                f"An unexpected error was encountered while parsing the Leaderboard response "
                f"{type(e).__name__}: {e}"
            )
            return LeaderboardObservationRound.ERROR_PAYLOAD

        return response_body

    @staticmethod
    def fix_api_data(data: Dict) -> Dict:
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

    def validate_api_data(self, data: Dict) -> bool:
        """Validates the API data format.

        :param data: the source data
        :returns: True on valid data, False otherwise
        """

        # Schema validation
        try:
            jsonschema.validate(
                instance=data,
                schema=SHEET_API_SCHEMA,
            )
        except jsonschema.exceptions.ValidationError:
            return False

        # Cell ranges match the configured ones
        data_ranges = set(i["range"] for i in data["valueRanges"])
        required_ranges = set(
            (self.params.leaderboard_points_range, self.params.leaderboard_layers_range)
        )
        if data_ranges != required_ranges:
            return False

        # Score thresholds are monotonic increasing
        for i in data["valueRanges"]:
            if i["range"] == self.params.leaderboard_layers_range:
                for layer_data in i["values"]:

                    # Check the layer and threshold format
                    if not all(re.match(THRESHOLD_REGEX, t) for t in layer_data):
                        return False

                    thresholds = [
                        int(img_data.split(":")[0]) for img_data in layer_data
                    ]

                    # Strictly increasing
                    if not all(x < y for x, y in zip(thresholds, thresholds[1:])):
                        return False

        return True


class ImageCodeCalculationBehaviour(DynamicNFTBaseBehaviour):
    """ImageCodeCalculationBehaviour"""

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
            api_data = LeaderboardObservationBehaviour.fix_api_data(
                self.synchronized_data.most_voted_api_data
            )
            leaderboard = api_data["leaderboard"]
            layer_data = api_data["layers"]
            thresholds = {k: list(v.keys()) for k, v in layer_data.items()}

            # Get the oldest (lowest id) token and previous score for each member
            member_to_token = {}
            for token_id, token_data in self.synchronized_data.token_to_data.items():
                if token_data["address"] not in member_to_token or int(token_id) < int(
                    member_to_token[token_data["address"]]["token_id"]
                ):
                    member_to_token[token_data["address"]] = {
                        "token_id": token_id,
                        "points": token_data["points"],
                    }

            self.context.logger.info(
                f"Member to token relationship is: {member_to_token}"
            )

            token_updates = {}
            for member, new_points in leaderboard.items():
                # Skip members in the leaderboard that have not minted an NFT
                if member not in member_to_token.keys():
                    continue
                if member_to_token[member]["points"] != new_points:
                    self.context.logger.info(
                        f"Calculating image code for member {member}: points={new_points} thresholds={thresholds}"
                    )
                    image_code = self.points_to_code(new_points, thresholds)
                    token_updates[member_to_token[member]["token_id"]] = {
                        "points": new_points,
                        "image_code": image_code,
                        "image_hash": None,  # Points have changed. This will be updated later.
                    }
                    self.context.logger.info(
                        f"New image code for member {member} [{new_points} points] is {image_code}"
                    )

            token_updates_serialized = json.dumps(token_updates, sort_keys=True)
            self.context.logger.info(
                f"Calculated token updates: {token_updates_serialized}"
            )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = ImageCodeCalculationPayload(
                self.context.agent_address, token_updates_serialized
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
        act_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, thresholds[ImageGenerationBehaviour.ImageManager.LAYER_NAMES[1]]
        )
        fr_code, points = ImageCodeCalculationBehaviour.get_layer_code(
            points, thresholds[ImageGenerationBehaviour.ImageManager.LAYER_NAMES[2]]
        )

        return cls_code + act_code + fr_code


class ImageGenerationBehaviour(DynamicNFTBaseBehaviour):
    """ImageGenerationBehaviour"""

    matching_round: Type[AbstractRound] = ImageGenerationRound

    def async_act(self) -> Generator:
        """Generate the images.

        Check if the changes list contains an image code
        that is not present in the token table. This happens when
        a member is granted a status whose corresponding image has never
        been used. For each of these cases, agents generate the new
        images and push them to IPFS.
        """
        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).local():
            # Get new layers from IPFS if needed
            # Ignored for now until it is tested further
            # self.update_layers()  # noqa: E800

            # In the current implementation, the image manager will be instanced every time the behaviour is run.
            # This is not ideal: a singleton or another pattern that avoids this might be more suited to our usecase.
            img_manager = self.ImageManager(logger=self.context.logger)

            # Get the image codes that have been never generated
            new_image_code_to_images = {}
            for update in self.synchronized_data.most_voted_token_updates.values():

                # Image already exists in the database
                if update["image_code"] in self.synchronized_data.image_code_to_hash:
                    continue

                self.context.logger.info(
                    f"Image {update['image_code']} does not exist. Generating..."
                )
                new_image_code_to_images[update["image_code"]] = img_manager.generate(
                    update["image_code"]
                )

            # If a single image fails to be generated we set this round as failed
            # This could have to do with corrupted API data so we do this to stay on the safe side
            if None in new_image_code_to_images.values():
                self.context.logger.info(
                    "An error happened while generating the new images"
                )
                status = "error"
                new_image_code_to_hash = {}
                images_in_ipfs = {}
            else:
                status = "success"
                # Push to IPFS
                new_image_code_to_hash = {}
                images_in_ipfs = {}
                for image_code, image in new_image_code_to_images.items():
                    image_path = Path(
                        img_manager.out_path, f"{image_code}.{img_manager.PNG_EXT}"
                    )
                    # Get image hash
                    # We first save the image as IPFSHashOnly.get() needs an existing file
                    # Once the image is pushed, it will be deleted
                    image.save(image_path)
                    self.context.logger.info(
                        f"Image {image_code} has been generated and saved at {image_path}"
                    )

                    self.context.logger.info(
                        f"Getting hash for image at {image_path}..."
                    )

                    image_hash = IPFSHashOnly.get(
                        str(image_path), cid_v1=True, wrap=False
                    )

                    self.context.logger.info(f"Image hash is {image_hash}...")

                    # Check whether the image is already present in the registry
                    image_url = f"{self.params.ipfs_gateway_base_url}{image_hash}"

                    image_in_ipfs = yield from self.check_ipfs_image(image_url)
                    if image_in_ipfs:
                        images_in_ipfs[image_code] = image_hash
                        continue

                    # Send
                    self.context.logger.info(
                        f"Trying to push image with hash {image_hash}..."
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

                    new_image_code_to_hash[image_code] = image_hash

            self.context.logger.info(
                f"Generated the following new images: {new_image_code_to_hash}\n"
                f"Found the following images already in IPFS: {images_in_ipfs}"
            )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = ImageGenerationPayload(
                self.context.agent_address,
                json.dumps(
                    {
                        "status": status,
                        "new_image_code_to_hash": new_image_code_to_hash,
                        "images_in_ipfs": images_in_ipfs,
                    },
                    sort_keys=True,
                ),
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def update_layers(self):  # pragma: no cover
        """Updates local layer if they dont match the ones from the leaderboard API"""
        api_data = LeaderboardObservationBehaviour.fix_api_data(
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
                IPFSHashOnly.get(image_file, cid_v1=True, wrap=False)
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

    def whitelist_hash(
        self, image_hash: str
    ) -> Generator[None, None, bool]:  # pragma: no cover
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

    def check_ipfs_image(self, img_url: str) -> Generator[None, None, bool]:
        """Check that the given ipfs hash exists in the registry

        :param img_hash: the image hash
        :param img_code: the image code
        :returns: True if image is present in the registry, False otherwise
        """

        # We just call to the mock url if this is an e2e test.
        # We need to figure a better way to avoid having this conditional here.
        if "mock_ipfs" in img_url:
            img_url = f"{self.params.ipfs_gateway_base_url}"

        self.context.logger.info(
            f"Checking if image already exists in the IPFS registry: {img_url}"
        )

        request_message, http_dialogue = self._build_http_request_message(
            method="GET", url=img_url
        )
        try:
            response = yield from self._do_request(
                request_message=request_message,
                http_dialogue=http_dialogue,
                timeout=HTTP_TIMEOUT,
            )

            if response.status_code != 200:
                self.context.logger.error(
                    f"Could not check image at {img_url}, code={response.status_code}"
                )
                return False

        except TimeoutException:
            return False

        self.context.logger.info(f"Image already exists at {img_url}")
        return True

    class ImageManager:
        """Class to load image layers and compose new images from them"""

        IMAGE_ROOT = Path(Path(__file__).parent, "data")
        LAYERS_DIR = "layers"
        IMAGES_DIR = "images"
        LAYER_NAMES = ("classes", "activation", "frames")
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

            img_layer_codes = [
                int(image_code[i : i + 2]) for i in range(0, len(image_code), 2)
            ]

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

            # Combine all other layers on top of the first one
            for i in range(1, len(img_layers)):
                img_layers[0].paste(img_layers[i], (0, 0), mask=img_layers[i])

            return img_layers[0]


class DBUpdateBehaviour(DynamicNFTBaseBehaviour):
    """DBUpdateBehaviour"""

    matching_round: Type[AbstractRound] = DBUpdateRound

    def async_act(self) -> Generator:
        """Update the database tables.

        User table: all entries whose points changed (the list from
        ImageCodeCalculationRound) must now reflect the new points and (if it applies)
        new image codes.

        Token table: must be updated now to reflect the new image redirects (if it applies).
        """
        last_update_time = cast(
            SharedState, self.context.state
        ).round_sequence.abci_app.last_timestamp.timestamp()

        self.context.logger.info(
            f"Current tokens: {self.synchronized_data.token_to_data}\n"
            f"Current images: {self.synchronized_data.image_code_to_hash}\n"
            f"Last update timestamp: {last_update_time}\n"
            f"Updating database tables. Updates: {self.synchronized_data.most_voted_token_updates}\n"
        )

        with self.context.benchmark_tool.measure(
            self.behaviour_id,
        ).consensus():
            payload = DBUpdatePayload(
                self.context.agent_address,
                json.dumps(
                    {"last_update_time": last_update_time},
                    sort_keys=True,
                ),
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class DynamicNFTRoundBehaviour(AbstractRoundBehaviour):
    """DynamicNFTRoundBehaviour"""

    initial_behaviour_cls = NewTokensBehaviour
    abci_app_cls = DynamicNFTAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        NewTokensBehaviour,
        LeaderboardObservationBehaviour,
        ImageCodeCalculationBehaviour,
        ImageGenerationBehaviour,
        DBUpdateBehaviour,
    ]
