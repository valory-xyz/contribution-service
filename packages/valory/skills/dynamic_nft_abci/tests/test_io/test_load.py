# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Tests for the loading functionality of abstract round abci."""

# pylint: skip-file

from pathlib import PosixPath
from typing import Dict, Optional, cast

import pytest
from PIL import ImageChops

from packages.valory.skills.dynamic_nft_abci.io_.load import (
    CustomLoaderType,
    Loader,
    PNGLoader,
    SupportedLoaderType,
)
from packages.valory.skills.dynamic_nft_abci.io_.store import (
    ExtendedSupportedFiletype,
    StoredPNGType,
)


class TestLoader:
    """Tests for the `Loader`."""

    def __dummy_custom_loader(self) -> None:
        """A dummy custom loading function to use for the tests."""

    @staticmethod
    @pytest.mark.parametrize(
        "filetype, custom_loader, expected_loader",
        (
            (None, None, None),
            (ExtendedSupportedFiletype.PNG, None, PNGLoader.load_single_object),
            (
                ExtendedSupportedFiletype.PNG,
                __dummy_custom_loader,
                PNGLoader.load_single_object,
            ),
            (None, __dummy_custom_loader, __dummy_custom_loader),
        ),
    )
    def test__get_loader_from_filetype(
        filetype: Optional[ExtendedSupportedFiletype],
        custom_loader: CustomLoaderType,
        expected_loader: Optional[SupportedLoaderType],
    ) -> None:
        """Test `_get_loader_from_filetype`."""
        if all(
            test_arg is None for test_arg in (filetype, custom_loader, expected_loader)
        ):
            with pytest.raises(
                ValueError,
                match="Please provide either a supported filetype or a custom loader function.",
            ):
                Loader(filetype, custom_loader)._get_single_loader_from_filetype()

        else:
            expected_loader = cast(SupportedLoaderType, expected_loader)
            loader = Loader(filetype, custom_loader)
            assert (
                loader._get_single_loader_from_filetype().__code__.co_code
                == expected_loader.__code__.co_code
            )

    @staticmethod
    def test_load(
        tmp_path: PosixPath,
        dummy_obj: StoredPNGType,
        dummy_multiple_obj: Dict[str, StoredPNGType],
    ) -> None:
        """Test `load`."""
        loader = Loader(ExtendedSupportedFiletype.PNG, None)

        # serialize dummy object.
        serialized_object = ":".join(
            [
                dummy_obj.mode,
                str(dummy_obj.size[0]),
                str(dummy_obj.size[1]),
                dummy_obj.tobytes().hex(),
            ]
        )
        # load with loader.
        loaded_obj = loader.load_single_object(serialized_object)
        # assert loaded png with expected.

        # Images with alpha channel can fail when compared directly
        # We use the approach from: https://stackoverflow.com/questions/35176639/compare-images-python-pil
        assert not ImageChops.difference(
            loaded_obj.convert("RGB"), dummy_obj.convert("RGB")
        ).getbbox()
