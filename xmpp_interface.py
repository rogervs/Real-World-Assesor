#!/usr/bin/env python3

# Slixmpp: The Slick XMPP Library
# Copyright (C) 2010  Nathanael C. Fritz
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.

import logging
from getpass import getpass
from argparse import ArgumentParser
from pydantic import BaseModel

import slixmpp

from typing import List, Optional
from audit import (
    State,
    Inspection,
    Audit,
    Auditor,
    test_setup,
    mock_responses,
)


class RWABot(slixmpp.ClientXMPP):

    """
    A bot that calls functions from XMPP commands
    """

    _audits: List[Audit] = []

    @property
    def audits(self):
        return self._audits

    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)

    async def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        await self.get_roster()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg["type"] in ("chat", "normal"):
            msg.reply(msg["from"].bare).send()
            # msg.reply("for sending\n%(body)s" % msg).send()
            # if msg["from"].bare in registered_users:
            #     print("User Registered")
            # else:
            #     print("User not registered")
            #     register_user(msg["from"].bare)
            #


if __name__ == "__main__":
    # Setup the command line arguments.
    parser = ArgumentParser(description=RWABot.__doc__)

    # Output verbosity options.
    parser.add_argument(
        "-q",
        "--quiet",
        help="set logging to ERROR",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
        default=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="set logging to DEBUG",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-p", "--password", dest="password", help="password to use")

    args = parser.parse_args()

    args.jid = "botty@foxhole"
    args.password = "botty"

    # Setup logging.
    logging.basicConfig(level=args.loglevel, format="%(levelname)-8s %(message)s")

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    # Setup the RWABot
    xmpp = RWABot(args.jid, args.password)

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
