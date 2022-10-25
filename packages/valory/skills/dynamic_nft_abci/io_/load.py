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

    def load_single_file(self, path: str) -> NativelySupportedSingleObjectType:
        """Read an image from a PNG file.

        :param path: the path of the png.
        :return: the image object.
        """
        try:
            return Image.open(path)
        except FileNotFoundError as e:  # pragma: no cover
            raise IOError(f"File {path} was not found!") from e
        except (UnidentifiedImageError, ValueError, TypeError) as e:  # pragma: no cover
            raise IOError("The provided png could not be opened and identified!") from e


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
        ] = PNGLoader().load_single_file
