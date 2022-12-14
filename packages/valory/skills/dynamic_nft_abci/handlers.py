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

"""This module contains the handlers for the skill of DynamicNFTAbciApp."""

import json
import re
from enum import Enum
from typing import cast
from urllib.parse import urlparse

from aea.protocols.base import Message

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler as BaseABCIRoundHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler as BaseContractApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    LedgerApiHandler as BaseLedgerApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    SigningHandler as BaseSigningHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    TendermintHandler as BaseTendermintHandler,
)
from packages.valory.skills.dynamic_nft_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
)
from packages.valory.skills.dynamic_nft_abci.models import SharedState
from packages.valory.skills.dynamic_nft_abci.rounds import SynchronizedData


ABCIRoundHandler = BaseABCIRoundHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
OK_CODE = 200
NOT_FOUND_CODE = 404
BAD_REQUEST_CODE = 400


class Route(Enum):
    """Handling route class"""

    HEALTH = "health"
    METADATA = "metadata"
    NONE = "none"


class HttpHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return SynchronizedData(
            db=self.context.state.round_sequence.latest_synchronized_data.db
        )

    def check_url(self, url) -> Route:
        """Check if an url is meant to be handled in this handler

        We expect url to match the pattern {hostname}/{token_id},
        where hostname is allowed to be localhost, 127.0.0.1 or the token_uri_base's hostname.
        Examples:
            localhost:8000/0
            127.0.0.1:8000/100
            https://pfp.staging.autonolas.tech/45
            http://pfp.staging.autonolas.tech/120

        :param url: the url to check
        :returns: True if the message is intended to be handled by this handler
        """
        uri_base_hostname = urlparse(self.context.params.token_uri_base).hostname
        METADATA_URL = rf".*({uri_base_hostname}|localhost|127.0.0.1)(:\d+)?\/\d+"
        HEALTH_URL = rf".*({uri_base_hostname}|localhost|127.0.0.1)(:\d+)?\/healthcheck"

        if re.match(METADATA_URL, url):
            return Route.METADATA

        if re.match(HEALTH_URL, url):
            return Route.HEALTH

        self.context.logger.info(
            f"The url {url} does not match the DynamicNFT HttpHandler's pattern"
        )
        return Route.NONE

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # Check if this is a request sent from the http_server skill
        if (
            http_msg.performative != HttpMessage.Performative.REQUEST
            or message.sender != str(HTTP_SERVER_PUBLIC_ID.without_hash())
        ):
            super().handle(message)
            return

        # Check if this message is for this skill. If not, send to super()
        # We expect requests to https://pfp.staging.autonolas.tech/{token_id}
        handler_route = self.check_url(http_msg.url)
        if handler_route == Route.NONE:
            super().handle(message)
            return

        # Retrieve dialogues
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))

        # Invalid message
        if http_dialogue is None:
            self.context.logger.info(
                "Received invalid http message={}, unidentified dialogue.".format(
                    http_msg
                )
            )
            return

        # Handle message
        self._handle_request(http_msg, http_dialogue, handler_route)

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue, handler_route: Route
    ) -> None:
        """
        Handle a Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.info(
            "Received http request with method={}, url={} and body={!r}".format(
                http_msg.method,
                http_msg.url,
                http_msg.body,
            )
        )
        if http_msg.method in ("get", "head"):
            if handler_route == Route.METADATA:
                self._handle_get_metadata(http_msg, http_dialogue)
            if handler_route == Route.HEALTH:
                self._handle_get_health(http_msg, http_dialogue)
        else:
            self._handle_non_get(http_msg, http_dialogue)  # reject other methods

    def _handle_get_metadata(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        # Get the requested uri and the token table
        request_uri = http_msg.url
        token_id = str(request_uri.split("/")[-1])
        token_to_data = self.synchronized_data.token_to_data

        if token_id not in token_to_data:
            self.context.logger.info(
                f"Requested URL {request_uri} is not present in token table"
            )

            http_response = http_dialogue.reply(
                performative=HttpMessage.Performative.RESPONSE,
                target_message=http_msg,
                version=http_msg.version,
                status_code=NOT_FOUND_CODE,
                status_text="Not found",
                headers=http_msg.headers,
                body=b"",
            )
        else:
            self.context.logger.info(
                f"Requested URL {request_uri} is present in token table"
            )

            image_hash = token_to_data[token_id]["image_hash"]

            # Build token metadata
            metadata = {
                "title": "Autonolas Contribute Badges",
                "name": f"Badge {token_id}",
                "description": "This NFT recognizes the contributions made by the holder to the Autonolas Community.",
                "image": f"ipfs://{image_hash}",
                "attributes": [],  # TODO: add attributes
            }

            self.context.logger.info(f"Responding with token metadata={metadata}")

            content_header = "Content-Type: application/json\n"

            http_response = http_dialogue.reply(
                performative=HttpMessage.Performative.RESPONSE,
                target_message=http_msg,
                version=http_msg.version,
                status_code=OK_CODE,
                status_text="Success",
                headers=f"{content_header}{http_msg.headers}",
                body=json.dumps(metadata).encode("utf-8"),
            )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_non_get(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request different from GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=BAD_REQUEST_CODE,
            status_text="Bad request",
            headers=http_msg.headers,
            body=b"",
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_get_health(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        last_update_time = self.synchronized_data.last_update_time

        if last_update_time:
            current_time = cast(
                SharedState, self.context.state
            ).round_sequence.abci_app.last_timestamp.timestamp()

            observation_interval = self.context.params.observation_interval

            seconds_since_last_reset = current_time - last_update_time
            seconds_until_next_update = (
                observation_interval - seconds_since_last_reset
            )  # this can be negative if we have passed the estimated reset time without resetting
            is_healthy = seconds_since_last_reset < 2 * observation_interval

        else:
            seconds_since_last_reset = None
            is_healthy = None
            seconds_until_next_update = None

        data = {
            "seconds_since_last_reset": seconds_since_last_reset,
            "healthy": is_healthy,
            "seconds_until_next_update": seconds_until_next_update,
        }

        self.context.logger.info(f"Responding with health data={data}")

        content_header = "Content-Type: application/json\n"

        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=OK_CODE,
            status_text="Success",
            headers=f"{content_header}{http_msg.headers}",
            body=json.dumps(data).encode("utf-8"),
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)
