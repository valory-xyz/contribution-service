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
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Type
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.crypto.ledger_apis import LedgerApis
from aea_cli_ipfs.ipfs_utils import IPFSDaemon

from packages.valory.contracts.ERC721Collective.contract import ERC721CollectiveContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.contract_api.custom_types import State
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import (
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.dynamic_nft_abci.behaviours import (
    DBUpdateBehaviour,
    DynamicNFTBaseBehaviour,
    ImageCodeCalculationBehaviour,
    ImageGenerationBehaviour,
    LeaderboardObservationBehaviour,
    NewMembersBehaviour,
    SYNDICATE_CONTRACT_ADDRESS,
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    Event,
    FinishedDBUpdateRound,
    NewMembersRound,
    SynchronizedData,
)


@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]:
    """Starts an IPFS daemon for the tests."""
    print("Starting IPFS daemon...")
    daemon = IPFSDaemon()
    daemon.start()
    yield daemon.is_started()
    print("Tearing down IPFS daemon...")
    daemon.stop()


use_ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")


DUMMY_LEADERBOARD = {
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A": 1500,
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525": 900,
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7": 575,
    "0x19B043aD06C48aeCb2028B0f10503422BD0E0918": 100,
    "0x7B394CD0B75f774c6808cc681b26aC3E5DF96E27": 3500,  # this one does not appear in the dummy members
}

DUMMY_LAYERS = {
    "classes": {
        0: "bafybeiauzyxtnahzul5gk27az7cb3evq5ttfwnxoi366lbrww3pcpthcmi",
        1000: "bafybeiay7owbbggi4nz4l4aeimzixia3v542iqcuaaiwd4kwsayu54aiqq",
        2000: "bafybeig35zr5r4e2gyc3c2ifkxnc43thyipmtgkauly7fxscut5r7zin2a",
        3000: "bafybeiea4in45zhx644yq4mzwrzjtqzzdgp7xv4ngv3ljttiwpgwldonl4",
        4000: "bafybeif6oacd3pkbpn4ij4daqpopjdehv2dv2tejpazwkdcs4cfvedlrvy",
    },
    "frames": {
        0: "bafybeifg2owpyplscve2sr4yjcjg6rxsooif2jqt4qmwvrbu36n5ehancm",
        1000: "bafybeige2swjq6fq6yvbvdhylkvfl7r3kv6nzwzqmkgb5g27ifziro342q",
        2000: "bafybeigyzhrhiybdsg3z7qn2nbqiyk52u4ytd6ndl6ixrdg3tk5g6owtsi",
    },
    "bars": {
        0: "bafybeig4corsme52qixcirhwuh6yquzd3bou3mgvjebspqxl2sh7jfpftq",
        200: "bafybeifrhbjmou67wn4uelixqxg732nhjmvgeb2w26czedsr4w2htactxy",
        500: "bafybeif3hvmq7rltk5hxucfnnazcwm4b2nuggquonaxhyx7rgsc3uhimye",
    },
}

DUMMY_THRESHOLDS = {"classes": [], "frames": [1000, 2000, 3000], "bars": [200, 500]}

DUMMY_API_DATA = {"leaderboard": DUMMY_LEADERBOARD, "layers": DUMMY_LAYERS}

DUMMY_API_RESPONSE = {
    "spreadsheetId": "1JYR9kfj_Zxd9xHX5AWSlO5X6HusFnb7p9amEUGU55Cg",
    "valueRanges": [
        {
            "range": "Leaderboard!A2:B102",
            "majorDimension": "ROWS",
            "values": [
                ["0x54EfA9b1865FFE8c528fb375A7A606149598932A", "1500"],
                ["0x3c03a080638b3c176aB7D9ed56E25bC416dFf525", "900"],
                ["0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7", "575"],
                ["0x19B043aD06C48aeCb2028B0f10503422BD0E0918", "100"],
                ["not_valid_address", "3500"],
            ],
        },
        {
            "range": "Layers!B1:Z3",
            "majorDimension": "ROWS",
            "values": [
                ["0:dummy_class_hash_0"],
                [
                    "0:dummy_frame_hash_0",
                    "1000:dummy_frame_hash_1",
                    "2000:dummy_frame_hash_2",
                    "3000:dummy_frame_hash_3",
                ],
                ["0:dummy_bar_hash_0", "200:dummy_bar_hash_1", "500:dummy_bar_hash_2"],
            ],
        },
    ],
}

DUMMY_BAD_API_RESPONSE = {}

SHEET_ID = "1JYR9kfj_Zxd9xHX5AWSlO5X6HusFnb7p9amEUGU55Cg"
GOOGLE_API_KEY = ""
GOOGLE_SHEETS_ENDPOINT = "https://sheets.googleapis.com/v4/spreadsheets"
DEFAULT_CELL_RANGE_POINTS = "Leaderboard!A2:B102"
DEFAULT_CELL_RANGE_LAYERS = "Layers!B1:Z3"

DEFAULT_SHEET_API_URL = (
    f"{GOOGLE_SHEETS_ENDPOINT}/{SHEET_ID}/values:batchGet?"
    f"ranges={DEFAULT_CELL_RANGE_POINTS}&ranges={DEFAULT_CELL_RANGE_LAYERS}&key={GOOGLE_API_KEY}"
)

DEFAULT_WHITELIST_URL = "https://ipfs-whitelist-admin.staging.autonolas.tech/whitelist"


def get_dummy_updates(error: bool = False) -> Dict:
    """Dummy updates"""
    if error:
        return {"dummy_member_1": {"points": 100, "image_code": "error_code"}}
    return {
        "dummy_member_1": {"points": 100, "image_code": "000100"},
        "dummy_member_2": {"points": 200, "image_code": "000102"},
    }


@dataclass
class BehaviourTestCase:
    """BehaviourTestCase"""

    name: str
    initial_data: Dict[str, Any]
    event: Event
    next_behaviour_class: Optional[Type[DynamicNFTBaseBehaviour]] = None


class BaseDynamicNFTTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parent.parent

    behaviour: DynamicNFTBaseBehaviour  # type: ignore
    behaviour_class: Type[DynamicNFTBaseBehaviour]
    next_behaviour_class: Type[DynamicNFTBaseBehaviour]
    synchronized_data: SynchronizedData
    done_event = Event.DONE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,  # type: ignore
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.behaviour_class.behaviour_id
        )

    def complete(self, event: Event) -> None:
        """Complete test"""

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )

    def teardown_class(self) -> None:
        """Teardown"""
        # Clean image output directory
        image_manager_cls = ImageGenerationBehaviour.ImageManager
        out_path = Path(image_manager_cls.IMAGE_ROOT, image_manager_cls.IMAGES_DIR)
        if os.path.isdir(out_path):
            shutil.rmtree(out_path)


class TestNewMembersBehaviour(BaseDynamicNFTTest):
    """Tests NewMembersBehaviour"""

    behaviour_class = NewMembersBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    def _mock_syndicate_contract_request(
        self,
        response_body: Dict,
        response_performative: ContractApiMessage.Performative,
    ) -> None:
        """Mock the WeightedPoolContract."""
        self.mock_contract_api_request(
            contract_id=str(ERC721CollectiveContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SYNDICATE_CONTRACT_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Happy path",
                    initial_data=dict(),
                    event=Event.DONE,
                ),
                {
                    "mock_response_data": dict(member_to_token_id={}),
                    "mock_response_performative": ContractApiMessage.Performative.STATE,
                },
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self._mock_syndicate_contract_request(
            response_body=kwargs.get("mock_response_data"),
            response_performative=kwargs.get("mock_response_performative"),
        )
        self.complete(test_case.event)


class TestNewMembersBehaviourContractError(TestNewMembersBehaviour):
    """Tests NewMembersBehaviour"""

    behaviour_class = NewMembersBehaviour
    next_behaviour_class = NewMembersBehaviour

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Contract error",
                    initial_data=dict(),
                    event=Event.CONTRACT_ERROR,
                ),
                {
                    "mock_response_data": dict(
                        member_to_token_id=NewMembersRound.ERROR_PAYLOAD
                    ),
                    "mock_response_performative": ContractApiMessage.Performative.ERROR,
                },
            )
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self._mock_syndicate_contract_request(
            response_body=kwargs.get("mock_response_data"),
            response_performative=kwargs.get("mock_response_performative"),
        )
        self.complete(test_case.event)


class TestLeaderboardObservationBehaviour(BaseDynamicNFTTest):
    """Tests LeaderboardObservationBehaviour"""

    behaviour_class = LeaderboardObservationBehaviour
    next_behaviour_class = ImageCodeCalculationBehaviour

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Happy path",
                    initial_data=dict(),
                    event=Event.DONE,
                ),
                {
                    "body": json.dumps(
                        DUMMY_API_RESPONSE,
                    ),
                    "status_code": 200,
                },
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                url=DEFAULT_SHEET_API_URL,
            ),
            response_kwargs=dict(
                version="",
                status_code=kwargs.get("status_code"),
                status_text="",
                headers="",
                body=kwargs.get("body").encode(),
            ),
        )
        self.complete(test_case.event)


class TestLeaderboardObservationErrorBehaviour(BaseDynamicNFTTest):
    """Tests LeaderboardObservationBehaviour"""

    behaviour_class = LeaderboardObservationBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Api code not 200",
                    initial_data=dict(),
                    event=Event.API_ERROR,
                ),
                {
                    "body": json.dumps(
                        {},
                    ),
                    "status_code": 404,
                },
            ),
            (
                BehaviourTestCase(
                    "Happy path",
                    initial_data=dict(),
                    event=Event.API_ERROR,
                ),
                {
                    "body": json.dumps(
                        DUMMY_BAD_API_RESPONSE,
                    ),
                    "status_code": 200,
                },
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                url=DEFAULT_SHEET_API_URL,
            ),
            response_kwargs=dict(
                version="",
                status_code=kwargs.get("status_code"),
                status_text="",
                headers="",
                body=kwargs.get("body").encode(),
            ),
        )
        self.complete(test_case.event)

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Force unexpected exception",
                    initial_data=dict(),
                    event=Event.API_ERROR,
                ),
                {
                    "body": json.dumps(
                        DUMMY_API_RESPONSE,
                    ),
                    "status_code": 200,
                },
            ),
        ],
    )
    def test_force_exception(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Force a exception for coverage purposes"""

        # Raise when is_valid_address() is called
        LedgerApis.is_valid_address = mock.Mock(
            side_effect=IndexError("dummy exception")
        )

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                url=DEFAULT_SHEET_API_URL,
            ),
            response_kwargs=dict(
                version="",
                status_code=kwargs.get("status_code"),
                status_text="",
                headers="",
                body=kwargs.get("body").encode(),
            ),
        )
        self.complete(test_case.event)


class TestImageCodeCalculationBehaviour(BaseDynamicNFTTest):
    """Tests ImageCodeCalculationBehaviour"""

    behaviour_class = ImageCodeCalculationBehaviour
    next_behaviour_class = ImageGenerationBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(most_voted_api_data=DUMMY_API_DATA),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)

    @pytest.mark.parametrize(
        "points, expected_code",
        [
            (0, "000000"),
            (150, "000000"),
            (999, "000000"),
            (1000, "000100"),
            (1999, "000102"),
            (2000, "000200"),
            (3750, "000302"),
            (10000, "000302"),
        ],
    )
    def test_points_to_code(self, points: float, expected_code: str) -> None:
        """Test the points_to_code function"""
        assert (
            ImageCodeCalculationBehaviour.points_to_code(points, DUMMY_THRESHOLDS)
            == expected_code
        )

    def test_points_to_code_negative(self) -> None:
        """Test the points_to_code function"""
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(-100, DUMMY_THRESHOLDS)


@use_ipfs_daemon
class TestImageGenerationBehaviour(BaseDynamicNFTTest):
    """Tests ImageGenerationBehaviour"""

    behaviour_class = ImageGenerationBehaviour
    next_behaviour_class = DBUpdateBehaviour

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup_class(
            param_overrides={"ipfs_domain_name": "/dns/localhost/tcp/5001/http"}
        )

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Happy path",
                    initial_data=dict(
                        most_voted_member_updates=get_dummy_updates(),
                        most_voted_api_data=DUMMY_API_DATA,
                    ),
                    event=Event.DONE,
                ),
                {
                    "status_code": 200,
                },
            )
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""

        # Create empty png files for the tests
        test_codes = [i["image_code"] for i in get_dummy_updates().values()]
        image_dir = Path(
            ImageGenerationBehaviour.ImageManager.IMAGE_ROOT,
            ImageGenerationBehaviour.ImageManager.IMAGES_DIR,
        )
        if not os.path.isdir(image_dir):
            os.makedirs(image_dir)
        for test_code in test_codes:
            open(Path(image_dir, f"{test_code}.png"), "w").close()

        # Hashes for these newly generated files
        EMPTY_FILE_HASHES = [
            "bafybeih6phzkblum5yvkyc527a6p324s2a23cjw3cqfg36wu7c2j7zg7ty",
            "bafybeidbxgqtmy65rls5jog5llm5fs3yfkhmt57wz4o4mefgrtosujrilu",
        ]

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()

        # Mock the IPFS whitelisting
        for hash_ in EMPTY_FILE_HASHES:
            WHITELIST_ENDPOINT = f"{DEFAULT_WHITELIST_URL}?hash={hash_}&key="

            self.mock_http_request(
                request_kwargs=dict(
                    method="POST",
                    headers="",
                    version="",
                    url=WHITELIST_ENDPOINT,
                ),
                response_kwargs=dict(
                    version="",
                    status_code=kwargs.get("status_code"),
                    status_text="",
                    headers="",
                    body=b"",
                ),
            )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=test_case.event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )

        shutil.rmtree(image_dir)

    @mock.patch.object(BaseBehaviour, "get_from_ipfs", return_value=False)
    def test_run_redownload_layers(self, *_: Any) -> None:
        """Run tests."""
        test_case = BehaviourTestCase(
            "Trigger image download from IPFS",
            initial_data=dict(
                most_voted_member_updates=get_dummy_updates(),
                most_voted_api_data=DUMMY_API_DATA,
            ),
            event=Event.DONE,
        )

        # Use an empty temporary directory as local image storage
        # so update_layers() detects that images are missing and tries to redownload
        with tempfile.TemporaryDirectory() as tmpdir:

            image_manager_cls = self.behaviour.behaviours[3].ImageManager
            image_manager_cls.IMAGE_ROOT = Path(tmpdir)

            # Create layer directory so it is removed
            layer_path = Path(tmpdir, image_manager_cls.LAYERS_DIR, "classes")
            os.makedirs(layer_path)

            # Create empty png files for the tests
            test_codes = [i["image_code"] for i in get_dummy_updates().values()]
            image_dir = Path(
                ImageGenerationBehaviour.ImageManager.IMAGE_ROOT,
                ImageGenerationBehaviour.ImageManager.IMAGES_DIR,
            )
            if not os.path.isdir(image_dir):
                os.makedirs(image_dir)
            for test_code in test_codes:
                open(Path(image_dir, f"{test_code}.png"), "w").close()

            # Hashes for these newly generated files
            EMPTY_FILE_HASHES = [
                "bafybeih6phzkblum5yvkyc527a6p324s2a23cjw3cqfg36wu7c2j7zg7ty",
                "bafybeidbxgqtmy65rls5jog5llm5fs3yfkhmt57wz4o4mefgrtosujrilu",
            ]

            self.fast_forward(test_case.initial_data)
            self.behaviour.act_wrapper()

            # Mock the IPFS whitelisting
            for hash_ in EMPTY_FILE_HASHES:
                WHITELIST_ENDPOINT = f"{DEFAULT_WHITELIST_URL}?hash={hash_}&key="

                self.mock_http_request(
                    request_kwargs=dict(
                        method="POST",
                        headers="",
                        version="",
                        url=WHITELIST_ENDPOINT,
                    ),
                    response_kwargs=dict(
                        version="",
                        status_code=200,
                        status_text="",
                        headers="",
                        body=b"",
                    ),
                )

            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(done_event=test_case.event)
            assert (
                self.behaviour.current_behaviour.behaviour_id  # type: ignore
                == self.next_behaviour_class.behaviour_id
            )

            shutil.rmtree(image_dir)


@use_ipfs_daemon
class TestImageGenerationErrorBehaviour(BaseDynamicNFTTest):
    """Tests ImageGenerationBehaviour"""

    behaviour_class = ImageGenerationBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup_class(
            param_overrides={"ipfs_domain_name": "/dns/localhost/tcp/5001/http"}
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Generation error",
                initial_data=dict(
                    most_voted_member_updates=get_dummy_updates(error=True),
                    most_voted_api_data=DUMMY_API_DATA,
                ),
                event=Event.IMAGE_ERROR,
            ),
        ],
    )
    def test_generation_error(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Happy path",
                    initial_data=dict(
                        most_voted_member_updates=get_dummy_updates(),
                        most_voted_api_data=DUMMY_API_DATA,
                    ),
                    event=Event.IMAGE_ERROR,
                ),
                {
                    "status_code": 404,
                },
            )
        ],
    )
    def test_whitelist_error(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""

        # Create empty png files for the tests
        test_codes = [i["image_code"] for i in get_dummy_updates().values()]
        image_dir = Path(
            ImageGenerationBehaviour.ImageManager.IMAGE_ROOT,
            ImageGenerationBehaviour.ImageManager.IMAGES_DIR,
        )
        if not os.path.isdir(image_dir):
            os.makedirs(image_dir)
        for test_code in test_codes:
            open(Path(image_dir, f"{test_code}.png"), "w").close()

        # Hashes for these newly generated files
        EMPTY_FILE_HASHES = [
            "bafybeih6phzkblum5yvkyc527a6p324s2a23cjw3cqfg36wu7c2j7zg7ty",
            "bafybeidbxgqtmy65rls5jog5llm5fs3yfkhmt57wz4o4mefgrtosujrilu",
        ]

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()

        # Mock the IPFS whitelisting

        WHITELIST_ENDPOINT = f"{DEFAULT_WHITELIST_URL}?hash={EMPTY_FILE_HASHES[0]}&key="

        self.mock_http_request(
            request_kwargs=dict(
                method="POST",
                headers="",
                version="",
                url=WHITELIST_ENDPOINT,
            ),
            response_kwargs=dict(
                version="",
                status_code=kwargs.get("status_code"),
                status_text="",
                headers="",
                body=b"",
            ),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=test_case.event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )

        shutil.rmtree(image_dir)


class TestDBUpdateBehaviour(BaseDynamicNFTTest):
    """Tests DBUpdateBehaviour"""

    behaviour_class = DBUpdateBehaviour
    next_behaviour_class = make_degenerate_behaviour(FinishedDBUpdateRound.round_id)

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data={},
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)


class TestImageManager:
    """TestImageManager"""

    def setup_class(self) -> None:
        """Setup class"""
        logger_mock = MagicMock()
        self.tmpdir = tempfile.TemporaryDirectory().name
        self.manager = ImageGenerationBehaviour.ImageManager(
            logger_mock, Path(self.tmpdir)
        )

    def test_generate_invalid_code_length(self) -> None:
        """test_generate_invalid_code_length"""
        assert not self.manager.generate("short")  # code too short

    def test_generate_invalid_code_non_existent(self) -> None:
        """test_generate_invalid_code_non_existent"""
        assert not self.manager.generate("090909")  # image does not exist

    def teardown_class(self) -> None:
        """Teardown class"""
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)
