import logging

from fastapi import FastAPI
from shared.logging import setup_logging

from src.databases import close_databases, setup_databases
from src.repositories import setup_repositories
from src.services import setup_services
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    app.state.ready = False
    setup_logging()
    await setup_databases(app)
    await setup_repositories(app)
    await setup_services(app)
    await setup_streams(app)
    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    app.state.ready = False
    await stop_streams(app)
    await close_databases(app)
    logging.info("Delivery service shut down.")
