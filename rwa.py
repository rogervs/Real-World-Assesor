#!/usr/bin/env python3

from fastapi import FastAPI
import logging
import asyncio

# import uvicorn
from uvicorn import Config, Server

from audit import Audit
from getpass import getpass
from argparse import ArgumentParser
from xmpp_interface import RWABot


# from xmpp_interface import *


app = FastAPI()


@app.post("/register/")
async def create_place_view(audit: Audit):

    xmpp.audits.append(audit)

    print(xmpp.audits)
    # return audit


if __name__ == "__main__":

    audits = []

    args = {}
    args["jid"] = "botty@foxhole"
    args["password"] = "botty"

    xmpp = RWABot(args["jid"], args["password"])
    # loop = asyncio.new_event_loop()

    xmpp.connect()
    # Connect to the XMPP server and start processing XMPP stanzas.

    # uvicorn.run("rwa:app", host="localhost", port=8000, loop="asyncio", debug=True)

    config = Config(app=app, loop=xmpp.loop)
    server = Server(config)

    # xmpp.process()
    # xmpp.loop.run_forever()
    xmpp.loop.run_until_complete(server.serve())
