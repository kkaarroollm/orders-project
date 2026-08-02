"""Shared library for orders-project microservices.

Import from the submodule that owns the symbol, e.g.::

    from shared.redis.publisher import StreamProducer
    from shared.db.repository import MongoRepository

Nothing is re-exported here on purpose: `shared.db` needs the `mongo` extra and
`shared.http_metrics` needs the `web` extra, so eager re-exports would force
every consumer to install both.
"""
