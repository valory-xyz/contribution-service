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

"""This module contains all the loading operations of the APY behaviour."""

from typing import Callable, Dict, Optional

from PIL import Image, UnidentifiedImageError

from packages.valory.skills.abstract_round_abci.io_.load import AbstractLoader
from packages.valory.skills.abstract_round_abci.io_.load import Loader as BaseLoader
from packages.valory.skills.dynamic_nft_abci.io_.store import (
    CustomObjectType,
    ExtendedSupportedFiletype,
    NativelySupportedSingleObjectType,
    SupportedSingleObjectType,
)


CustomLoaderType = Optional[Callable[[str], CustomObjectType]]
SupportedLoaderType = Callable[[str], SupportedSingleObjectType]


class PNGLoader(AbstractLoader):
    """A PNG files Loader."""

    def load_single_object(
        self, serialized_object: str
    ) -> NativelySupportedSingleObjectType:
        """Load a single object."""
        mode, width, height, data = serialized_object.split(":")
        size = (int(width), int(height))
        return Image.frombytes(mode, size, bytes.fromhex(data))


class Loader(BaseLoader):
    """Class which loads files."""

    def __init__(
        self,
        filetype: Optional[ExtendedSupportedFiletype],
        custom_loader: CustomLoaderType,
    ):
        """Initialize a `Loader`."""
        super().__init__(filetype, custom_loader)

        self.__filetype_to_loader: Dict[ExtendedSupportedFiletype, SupportedLoaderType]
        self.__filetype_to_loader[
            ExtendedSupportedFiletype.PNG
        ] = PNGLoader().load_single_object
