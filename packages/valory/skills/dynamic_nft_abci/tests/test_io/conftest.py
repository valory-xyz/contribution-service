# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Conftest module for io tests."""

# pylint: skip-file

from pathlib import Path
from typing import Dict

import pytest
from PIL import Image

from packages.valory.skills.dynamic_nft_abci.behaviours import IMAGE_ROOT
from packages.valory.skills.dynamic_nft_abci.io_.store import StoredPNGType


@pytest.fixture
def dummy_obj() -> StoredPNGType:
    """A dummy custom object to test the storing with."""
    return Image.open(Path(IMAGE_ROOT, "layers", "classes", "Gli.png"))


@pytest.fixture
def dummy_multiple_obj(dummy_obj: StoredPNGType) -> Dict[str, StoredPNGType]:
    """Many dummy custom objects to test the storing with."""
    return {f"test_obj_{i}.png": dummy_obj for i in range(10)}
