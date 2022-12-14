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

import copy
import datetime
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Type, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.crypto.ledger_apis import LedgerApis
from aea_cli_ipfs.ipfs_utils import IPFSDaemon

from packages.valory.contracts.dynamic_contribution.contract import (
    DynamicContributionContract,
)
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
    DEFAULT_IMAGE_CODE,
    DEFAULT_POINTS,
    DynamicNFTBaseBehaviour,
    ImageCodeCalculationBehaviour,
    ImageGenerationBehaviour,
    LeaderboardObservationBehaviour,
    NewTokensBehaviour,
)
from packages.valory.skills.dynamic_nft_abci.models import SharedState
from packages.valory.skills.dynamic_nft_abci.rounds import (
    Event,
    FinishedDBUpdateRound,
    NewTokensRound,
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

DYNAMIC_CONTRIBUTION_CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
BASIC_IMAGE_CID = "basic_image_cid"

DUMMY_TOKEN_TO_DATA = {
    1: {
        "address": "0x54EfA9b1865FFE8c528fb375A7A606149598932A",
        "points": DEFAULT_POINTS,
        "image_code": DEFAULT_IMAGE_CODE,
        "image_hash": BASIC_IMAGE_CID,
    },
    2: {
        "address": "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525",
        "points": DEFAULT_POINTS,
        "image_code": DEFAULT_IMAGE_CODE,
        "image_hash": BASIC_IMAGE_CID,
    },
    3: {
        "address": "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7",
        "points": DEFAULT_POINTS,
        "image_code": DEFAULT_IMAGE_CODE,
        "image_hash": BASIC_IMAGE_CID,
    },
    4: {
        "address": "0x19B043aD06C48aeCb2028B0f10503422BD0E0918",
        "points": DEFAULT_POINTS,
        "image_code": DEFAULT_IMAGE_CODE,
        "image_hash": BASIC_IMAGE_CID,
    },
    5: {
        "address": "0x8325c5e4a56E352355c590E4A43420840F067F98",
        "points": DEFAULT_POINTS,
        "image_code": DEFAULT_IMAGE_CODE,
        "image_hash": BASIC_IMAGE_CID,
    },  # this one does not appear in the dummy leaderboard
}


DUMMY_LEADERBOARD = {
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A": 1500,
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525": 900,
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7": 575,
    "0x7B394CD0B75f774c6808cc681b26aC3E5DF96E27": 3500,  # this one does not appear in the dummy members
}

DUMMY_ADDRESSES = [
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A",
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525",
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7",
    "0x7B394CD0B75f774c6808cc681b26aC3E5DF96E27",
    "0x54EfA9b1865FFE8c528fb375A7A606149598932A",  # addresses are repeated
    "0x3c03a080638b3c176aB7D9ed56E25bC416dFf525",
    "0x44704AE66f0B9FF08a7b0584B49FE941AdD1bAE7",
    "0x7B394CD0B75f774c6808cc681b26aC3E5DF96E27",
]

DUMMY_TOKEN_ID_TO_MEMBER = {i: member for i, member in enumerate(DUMMY_ADDRESSES)}

DUMMY_LAYERS = {
    "classes": {
        0: "bafybeif4dtvtnqjss4dhmwenxzhbyao6reqoxx5imlzxgxeh4bajnz444u",
    },
    "activation": {
        0: "bafybeicy22hgzs7kwuw7wswht2q3gmv4daxyoga2mvr5f644lgzfconpn4",
        100: "bafybeibhfdzlez66uyeofhz3z4sq6an64i6b2cvadvzahb5iygqyq4gscu",
    },
    "frames": {
        0: "bafybeicy22hgzs7kwuw7wswht2q3gmv4daxyoga2mvr5f644lgzfconpn4",
        49900: "bafybeih67y7g5qstirprambfsqd7dbunyyjlktpfqpukabp4fkrt4ziuba",
        99900: "bafybeibiyqmsjgp7ofqktthkgi6up77w4mzrgyzii2mtiodic6h7v2h6de",
        149900: "bafybeiheikuwkkwaygtssfkumzhursxh6a76546spakmr6wwrw6v3heb2a",
    },
}

DUMMY_THRESHOLDS = {
    k: list(sorted(DUMMY_LAYERS[k].keys())) for k in DUMMY_LAYERS.keys()
}

DUMMY_API_DATA = {"leaderboard": DUMMY_LEADERBOARD, "layers": DUMMY_LAYERS}

DUMMY_API_RESPONSE = {
    "spreadsheetId": "1m7jUYBoK4bFF0F2ZRnT60wUCAMWGMJ_ZfALsLfW5Dxc",
    "valueRanges": [
        {
            "range": "Ranking!B2:C302",
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
            ],
        },
    ],
}

DUMMY_BAD_API_RESPONSE = {}
DUMMY_BAD_API_RESPONSE_WRONG_RANGES = copy.deepcopy(DUMMY_API_RESPONSE)
DUMMY_BAD_API_RESPONSE_WRONG_RANGES["valueRanges"][0]["range"] = "wrong_range"
DUMMY_BAD_API_RESPONSE_WRONG_THRESHOLDS = copy.deepcopy(DUMMY_API_RESPONSE)
DUMMY_BAD_API_RESPONSE_WRONG_THRESHOLDS["valueRanges"][1]["values"][1][
    0
] = "10000:dummy_frame_hash_0"

SHEET_ID = "1m7jUYBoK4bFF0F2ZRnT60wUCAMWGMJ_ZfALsLfW5Dxc"
GOOGLE_API_KEY = None
GOOGLE_SHEETS_ENDPOINT = "https://sheets.googleapis.com/v4/spreadsheets"
DEFAULT_CELL_RANGE_POINTS = "Ranking!B2:C302"
DEFAULT_CELL_RANGE_LAYERS = "Layers!B1:Z3"

DEFAULT_SHEET_API_URL = (
    f"{GOOGLE_SHEETS_ENDPOINT}/{SHEET_ID}/values:batchGet?"
    f"ranges={DEFAULT_CELL_RANGE_POINTS}&ranges={DEFAULT_CELL_RANGE_LAYERS}&key={GOOGLE_API_KEY}"
)

MOCK_SHEET_API_URL = "http://localhost:3000/mock_sheet_id"

DEFAULT_WHITELIST_URL = "http://localhost"

IMAGE_PATH = Path(
    ImageGenerationBehaviour.ImageManager.IMAGE_ROOT,
    ImageGenerationBehaviour.ImageManager.IMAGES_DIR,
)

IPFS_GATEWAY_BASE_URL = "https://gateway.staging.autonolas.tech/ipfs/"

IMAGE_CODE_TO_HASHES = {
    "000000": "bafybeiabtdl53v2a3irrgrg7eujzffjallpymli763wvhv6gceurfmcemm",
    "000100": "bafybeid46w6yzbehir7ackcnsyuasdkun5aq7jnckt4sknvmiewpph776q",
    "000101": "bafybeigbxlwzljbxnlwteupmt6c6k7k2m4bbhunvxxa53dc7niuedilnr4",
    "000102": "bafybeiawxpq4mqckbau3mjwzd3ic2o7ywlhp6zqo7jnaft26zeqm3xsjjy",
    "000103": "bafybeie6k53dupf7rf6622rzfxu3dmlv36hytqrmzs5yrilxwcrlhrml2m",
}


def get_dummy_updates(error: bool = False) -> Dict:
    """Dummy updates"""
    if error:
        return {"dummy_member_1": {"points": 1000, "image_code": "error_code"}}
    return {
        "dummy_member_1": {"points": 55000, "image_code": "000101"},
        "dummy_member_2": {"points": 105000, "image_code": "000102"},
    }


def get_dummy_images() -> Dict:
    """Dummy updates"""
    return {i["image_code"]: "dummy_cid" for i in get_dummy_updates().values()}


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
    image_dir: Path

    def setup(self, **kwargs: Any) -> None:
        """Setup test"""
        super().setup(**kwargs)
        self.image_dir = IMAGE_PATH
        Path(self.image_dir).mkdir()

    def teardown(self) -> None:
        """Teardown test"""
        super().teardown()
        shutil.rmtree(self.image_dir)

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


class TestNewTokensBehaviour(BaseDynamicNFTTest):
    """Tests NewTokensBehaviour"""

    behaviour_class = NewTokensBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    def _mock_dynamic_contribution_contract_request(
        self,
        response_body: Dict,
        response_performative: ContractApiMessage.Performative,
    ) -> None:
        """Mock the WeightedPoolContract."""
        self.mock_contract_api_request(
            contract_id=str(DynamicContributionContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=DYNAMIC_CONTRIBUTION_CONTRACT_ADDRESS,
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
                    "mock_response_data": dict(
                        token_id_to_member=DUMMY_TOKEN_ID_TO_MEMBER
                    ),
                    "mock_response_performative": ContractApiMessage.Performative.STATE,
                },
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()
        self._mock_dynamic_contribution_contract_request(
            response_body=kwargs.get("mock_response_data"),
            response_performative=kwargs.get("mock_response_performative"),
        )
        self.complete(test_case.event)


class TestNewTokensBehaviourContractError(TestNewTokensBehaviour):
    """Tests NewTokensBehaviour"""

    behaviour_class = NewTokensBehaviour
    next_behaviour_class = NewTokensBehaviour

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
                        member_to_token_id=NewTokensRound.ERROR_PAYLOAD
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
        self._mock_dynamic_contribution_contract_request(
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
                    "Wrong API response: empty dict",
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
            (
                BehaviourTestCase(
                    "Wrong API response: wrong range",
                    initial_data=dict(),
                    event=Event.API_ERROR,
                ),
                {
                    "body": json.dumps(
                        DUMMY_BAD_API_RESPONSE_WRONG_RANGES,
                    ),
                    "status_code": 200,
                },
            ),
            (
                BehaviourTestCase(
                    "Wrong API response: wrong thresholds",
                    initial_data=dict(),
                    event=Event.API_ERROR,
                ),
                {
                    "body": json.dumps(
                        DUMMY_BAD_API_RESPONSE_WRONG_THRESHOLDS,
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
        """Force an exception for coverage purposes"""

        # Raise when is_valid_address() is called
        with mock.patch.object(
            LedgerApis, "is_valid_address", side_effect=IndexError("dummy exception")
        ):
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


class TestLeaderboardObservationURLMockBehaviour(BaseDynamicNFTTest):
    """Tests LeaderboardObservationBehaviour"""

    behaviour_class = LeaderboardObservationBehaviour
    next_behaviour_class = ImageCodeCalculationBehaviour

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup_class(
            param_overrides={
                "leaderboard_endpoint": MOCK_SHEET_API_URL,
            }
        )

    @pytest.mark.parametrize(
        "test_case, kwargs",
        [
            (
                BehaviourTestCase(
                    "Happy path with mocked e2e api url",
                    initial_data=dict(),
                    event=Event.DONE,
                ),
                {
                    "body": json.dumps(
                        DUMMY_API_RESPONSE,
                    ),
                    "status_code": 200,
                    "api_url": MOCK_SHEET_API_URL,
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
                url=kwargs.get("api_url"),
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
                initial_data=dict(
                    token_to_data=DUMMY_TOKEN_TO_DATA,
                    most_voted_api_data=DUMMY_API_DATA,
                ),
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
            (150, "000100"),
            (50000, "000101"),
            (100000, "000102"),
            (120000, "000102"),
            (145000, "000102"),
            (150000, "000103"),
            (200000, "000103"),
            (205000, "000103"),
        ],
    )
    def test_points_to_code(self, points: float, expected_code: str) -> None:
        """Test the points_to_code function"""
        code = ImageCodeCalculationBehaviour.points_to_code(points, DUMMY_THRESHOLDS)
        assert code == expected_code, f"Expected {expected_code}, got {code}"

    def test_points_to_code_negative(self) -> None:
        """Test the points_to_code function"""

        # Points must be positive
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(-100, DUMMY_THRESHOLDS)

        THRESHOLDS = {
            "classes": [100],
            "frames": [100, 1000, 2000, 3000],
            "bars": [100, 200, 500],
        }

        # Points must be higher than thresholds[0]
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(0, THRESHOLDS)

        THRESHOLDS = {
            "classes": [],
            "frames": [],
            "bars": [],
        }

        # Thresholds can't be empty
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(0, THRESHOLDS)


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
                        most_voted_token_updates=get_dummy_updates(),
                        most_voted_api_data=DUMMY_API_DATA,
                    ),
                    event=Event.DONE,
                ),
                {
                    "status_code": 200,
                    "mock_http": True,
                },
            ),
            (
                BehaviourTestCase(
                    "Happy path: images not in registry",
                    initial_data=dict(
                        most_voted_token_updates=get_dummy_updates(),
                        most_voted_api_data=DUMMY_API_DATA,
                    ),
                    event=Event.DONE,
                ),
                {
                    "status_code": 404,
                    "mock_http": True,
                },
            ),
            (
                BehaviourTestCase(
                    "Happy path: images already in database",
                    initial_data=dict(
                        most_voted_token_updates=get_dummy_updates(),
                        most_voted_api_data=DUMMY_API_DATA,
                        images=get_dummy_images(),
                    ),
                    event=Event.DONE,
                ),
                {
                    "status_code": 200,
                    "mock_http": False,
                },
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase, kwargs: Any) -> None:
        """Run tests."""

        # Create empty png files for the tests
        test_codes = [i["image_code"] for i in get_dummy_updates().values()]
        for test_code in test_codes:
            open(Path(self.image_dir, f"{test_code}.png"), "w").close()

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()

        # Mock the IPFS checks
        if kwargs.get("mock_http"):
            for img_code in test_codes:

                img_hash = IMAGE_CODE_TO_HASHES[img_code]

                url = f"{IPFS_GATEWAY_BASE_URL}{img_hash}"

                self.mock_http_request(
                    request_kwargs=dict(
                        method="GET",
                        headers="",
                        version="",
                        url=url,
                    ),
                    response_kwargs=dict(
                        version="",
                        status_code=kwargs.get("status_code"),
                        status_text="",
                        headers="",
                        body=b"",
                    ),
                )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=test_case.event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )

    @mock.patch.object(BaseBehaviour, "get_from_ipfs", return_value=False)
    def test_run_redownload_layers(self, *_: Any) -> None:
        """Run tests."""

        test_case = BehaviourTestCase(
            "Trigger image download from IPFS",
            initial_data=dict(
                most_voted_token_updates=get_dummy_updates(),
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
            for test_code in test_codes:
                open(Path(self.image_dir, f"{test_code}.png"), "w").close()

            self.fast_forward(test_case.initial_data)
            self.behaviour.act_wrapper()

            # Mock the IPFS checks
            for img_code in test_codes:

                img_hash = IMAGE_CODE_TO_HASHES[img_code]

                url = f"{IPFS_GATEWAY_BASE_URL}{img_hash}"

                self.mock_http_request(
                    request_kwargs=dict(
                        method="GET",
                        headers="",
                        version="",
                        url=url,
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
                    most_voted_token_updates=get_dummy_updates(error=True),
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
                        most_voted_token_updates=get_dummy_updates(),
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
        for test_code in test_codes:
            open(Path(self.image_dir, f"{test_code}.png"), "w").close()

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()

        # Mock the IPFS checks
        for img_code in test_codes:

            img_hash = IMAGE_CODE_TO_HASHES[img_code]

            url = f"{IPFS_GATEWAY_BASE_URL}{img_hash}"

            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    headers="",
                    version="",
                    url=url,
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

    @mock.patch.object(BaseBehaviour, "send_to_ipfs", return_value=None)
    def test_send_to_ipfs_error(self, *_: Any) -> None:
        """Run tests."""

        test_case = BehaviourTestCase(
            "Happy path",
            initial_data=dict(
                most_voted_token_updates=get_dummy_updates(),
                most_voted_api_data=DUMMY_API_DATA,
            ),
            event=Event.IMAGE_ERROR,
        )

        # Create empty png files for the tests
        test_codes = [i["image_code"] for i in get_dummy_updates().values()]
        for test_code in test_codes:
            open(Path(self.image_dir, f"{test_code}.png"), "w").close()

        self.fast_forward(test_case.initial_data)
        self.behaviour.act_wrapper()

        # Mock the IPFS checks
        for img_code in test_codes[:1]:  # We'll fail on the first try

            img_hash = IMAGE_CODE_TO_HASHES[img_code]

            url = f"{IPFS_GATEWAY_BASE_URL}{img_hash}"

            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    headers="",
                    version="",
                    url=url,
                ),
                response_kwargs=dict(
                    version="",
                    status_code=404,
                    status_text="",
                    headers="",
                    body=b"",
                ),
            )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=test_case.event)
        assert (
            self.behaviour.current_behaviour.behaviour_id  # type: ignore
            == self.next_behaviour_class.behaviour_id
        )


class TestDBUpdateBehaviour(BaseDynamicNFTTest):
    """Tests DBUpdateBehaviour"""

    behaviour_class = DBUpdateBehaviour
    next_behaviour_class = make_degenerate_behaviour(FinishedDBUpdateRound.round_id)

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data={"most_voted_token_updates": {}},
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        time_in_future = datetime.datetime.now() + datetime.timedelta(hours=10)
        state = cast(SharedState, self._skill.skill_context.state)
        state.round_sequence.abci_app.update_time(time_in_future)
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
