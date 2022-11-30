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

"""Test the handlers.py module of the DynamicNFT skill."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, cast
from unittest.mock import patch

import pytest
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.dynamic_nft_abci.dialogues import HttpDialogues
from packages.valory.skills.dynamic_nft_abci.handlers import (
    BAD_REQUEST_CODE,
    HttpHandler,
    NOT_FOUND_CODE,
    TEMPORARY_REDIRECT_CODE,
)


PACKAGE_DIR = Path(__file__).parent.parent

HTTP_SERVER_SENDER = str(HTTP_SERVER_PUBLIC_ID.without_hash())

TOKEN_URI_BASE = "https://pfp.autonolas.network/"  # nosec


@dataclass
class HandlerTestCase:
    """HandlerTestCase"""

    name: str
    request_url: str
    redirects: Dict[str, str]
    response_status_code: int
    response_status_text: str
    response_headers: str


class TestHttpHandler(BaseSkillTestCase):
    """Test HttpHandler of http_echo."""

    path_to_skill = PACKAGE_DIR

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        super().setup_class()
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.logger = cls._skill.skill_context.logger

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.get_method = "get"
        cls.post_method = "post"
        cls.url = f"{TOKEN_URI_BASE}0"
        cls.url_redirect = "some_url_redirect"
        cls.version = "some_version"
        cls.headers = "some_headers"
        cls.body = b"some_body/"
        cls.sender = HTTP_SERVER_SENDER
        cls.skill_id = str(cls._skill.skill_context.skill_id)

        cls.status_code = 100
        cls.status_text = "some_status_text"

        cls.content = b"some_content"
        cls.list_of_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": cls.get_method,
                    "url": cls.url,
                    "version": cls.version,
                    "headers": cls.headers,
                    "body": cls.body,
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the http_echo handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the http_echo handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.REQUEST,
            to=self.skill_id,
            method=self.get_method,
            url=self.url,
            version=self.version,
            headers=self.headers,
            body=self.body,
            sender=HTTP_SERVER_SENDER,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"Received invalid http message={incoming_message}, unidentified dialogue.",
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            HandlerTestCase(
                name="uri in redirects",
                request_url=f"{TOKEN_URI_BASE}0",
                redirects={"0": "some_url_redirect"},
                response_status_code=TEMPORARY_REDIRECT_CODE,
                response_status_text="Temporary redirect",
                response_headers="Location: some_url_redirect\nsome_headers",
            ),
            HandlerTestCase(
                name="uri not in redirects",
                request_url=f"{TOKEN_URI_BASE}1",
                redirects={},
                response_status_code=NOT_FOUND_CODE,
                response_status_text="Not found",
                response_headers="some_headers",
            ),
        ],
    )
    def test_handle_request_get(self, test_case):
        """Test the _handle_request method of the http_echo handler where method is get."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method=self.get_method,
                url=test_case.request_url,
                version=self.version,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(
                self.http_handler.context.state, "_round_sequence"
            ) as mock_round_sequence:
                mock_round_sequence.latest_synchronized_data.db = {
                    "redirects": test_case.redirects
                }
                self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "Received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_get
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=test_case.response_status_code,
            status_text=test_case.response_status_text,
            headers=test_case.response_headers,
            body=b"",
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Responding with: {message}",
        )

    def test_handle_request_post(self):
        """Test the _handle_request method of the http_echo handler where method is post."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method=self.post_method,
                url=self.url,
                version=self.version,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "Received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_non_get
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=BAD_REQUEST_CODE,
            status_text="Bad request",
            headers=incoming_message.headers,
            body=b"",
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Responding with: {message}",
        )

    def test_teardown(self):
        """Test the teardown method of the http_echo handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
