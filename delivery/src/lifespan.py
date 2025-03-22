import logging

from fastapi import FastAPI

from src.common import setup_logging
from src.databases import close_databases, setup_databases
from src.repositories import setup_repositories
from src.services import setup_services
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to DB & initialize resources."""
    app.state.ready = False
    setup_logging()

    await setup_databases(app)
    await setup_repositories(app)
    await setup_services(app)
    await setup_streams(app)

    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    """Gracefully cancel tasks and close DB connections."""
    app.state.ready = False
    await stop_streams(app)
    await close_databases(app)

    logging.info("Delivery service shut down.")
