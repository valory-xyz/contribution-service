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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Type

import pytest
from aea_cli_ipfs.ipfs_utils import IPFSDaemon

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
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
)
from packages.valory.skills.dynamic_nft_abci.rounds import (
    Event,
    FinishedDBUpdateRound,
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
        1: "bafybeiay7owbbggi4nz4l4aeimzixia3v542iqcuaaiwd4kwsayu54aiqq",
        2: "bafybeig35zr5r4e2gyc3c2ifkxnc43thyipmtgkauly7fxscut5r7zin2a",
        3: "bafybeiea4in45zhx644yq4mzwrzjtqzzdgp7xv4ngv3ljttiwpgwldonl4",
        4: "bafybeif6oacd3pkbpn4ij4daqpopjdehv2dv2tejpazwkdcs4cfvedlrvy",
    },
    "frames": {
        0: "bafybeifg2owpyplscve2sr4yjcjg6rxsooif2jqt4qmwvrbu36n5ehancm",
        1: "bafybeige2swjq6fq6yvbvdhylkvfl7r3kv6nzwzqmkgb5g27ifziro342q",
        2: "bafybeigyzhrhiybdsg3z7qn2nbqiyk52u4ytd6ndl6ixrdg3tk5g6owtsi",
    },
    "bars": {
        0: "bafybeig4corsme52qixcirhwuh6yquzd3bou3mgvjebspqxl2sh7jfpftq",
        1: "bafybeifrhbjmou67wn4uelixqxg732nhjmvgeb2w26czedsr4w2htactxy",
        2: "bafybeif3hvmq7rltk5hxucfnnazcwm4b2nuggquonaxhyx7rgsc3uhimye",
    },
}

DUMMY_API_DATA = {"leaderboard": DUMMY_LEADERBOARD, "layers": DUMMY_LAYERS}

SHEET_ID = "1JYR9kfj_Zxd9xHX5AWSlO5X6HusFnb7p9amEUGU55Cg"
GOOGLE_API_KEY = ""
GOOGLE_SHEETS_ENDPOINT = "https://sheets.googleapis.com/v4/spreadsheets"
DEFAULT_CELL_RANGE_POINTS = "Leaderboard!A2:B102"
DEFAULT_CELL_RANGE_LAYERS = "Layers!B1:Z3"

DEFAULT_SHEET_API_URL = (
    f"{GOOGLE_SHEETS_ENDPOINT}/{SHEET_ID}/values:batchGet?"
    f"ranges={DEFAULT_CELL_RANGE_POINTS}&ranges={DEFAULT_CELL_RANGE_LAYERS}&key={GOOGLE_API_KEY}"
)


def get_dummy_updates() -> Dict:
    """Dummy updates"""
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


class TestNewMembersBehaviour(BaseDynamicNFTTest):
    """Tests NewMembersBehaviour"""

    behaviour_class = NewMembersBehaviour
    next_behaviour_class = LeaderboardObservationBehaviour

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(),
                event=Event.DONE,
            ),
        ],
    )
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""
        self.fast_forward(test_case.initial_data)
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
                        DUMMY_API_DATA,
                    ),
                    "status_code": 200,
                },
            )
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
        assert ImageCodeCalculationBehaviour.points_to_code(points) == expected_code

    def test_points_to_code_negative(self) -> None:
        """Test the points_to_code function"""
        with pytest.raises(ValueError):
            assert ImageCodeCalculationBehaviour.points_to_code(-100)


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
        "test_case",
        [
            BehaviourTestCase(
                "Happy path",
                initial_data=dict(
                    most_voted_member_updates=get_dummy_updates(),
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
