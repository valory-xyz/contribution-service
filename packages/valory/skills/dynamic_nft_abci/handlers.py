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

from typing import cast

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


ABCIRoundHandler = BaseABCIRoundHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler

TEMPORARY_REDIRECT_CODE = 307
NOT_FOUND_CODE = 404
BAD_REQUEST_CODE = 400


class HttpHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # Check if this message is for this skill. If not, send to super()
        # We expect requests to https://pfp.autonolas.network/{token_id}
        if (
            http_msg.performative != HttpMessage.Performative.REQUEST
            or message.sender != str(HTTP_SERVER_PUBLIC_ID.without_hash())
            or "nft_id" not in http_msg.url
        ):
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
        self._handle_request(http_msg, http_dialogue)

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
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
            self._handle_get(http_msg, http_dialogue)
        else:
            self._handle_non_get(http_msg, http_dialogue)  # reject other methods

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        # Get the requested uri and the redirects table
        request_uri = http_msg.url
        token_id = request_uri.split("/")[-1]
        redirects = self.context.state.round_sequence.latest_synchronized_data.redirects

        self.context.logger.info(
            f"Check token_id: {token_id} in {list(redirects.keys())}"
        )

        # Check if the uri exists in the redirect table
        if token_id not in redirects:
            self.context.logger.info(
                f"Requested URL {request_uri} is not present in redirect table"
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
                f"Requested URL {request_uri} is present in redirect table"
            )

            redirect_uri = redirects[token_id]
            location_headers = f"Location: {redirect_uri}\n"

            http_response = http_dialogue.reply(
                performative=HttpMessage.Performative.RESPONSE,
                target_message=http_msg,
                version=http_msg.version,
                status_code=TEMPORARY_REDIRECT_CODE,
                status_text="Temporary redirect",
                headers=f"{location_headers}{http_msg.headers}",
                body=b"",
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
