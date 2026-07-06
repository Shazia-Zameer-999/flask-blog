"""Lazy MongoDB connection helpers."""

from flask import current_app
from pymongo import MongoClient


def get_db():
    """Return the configured database without connecting during imports."""
    client = current_app.extensions.get("mongo_client")
    if client is None:
        uri = current_app.config.get("MONGO_URI")
        if not uri:
            raise RuntimeError("MONGO_URI is not configured")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        current_app.extensions["mongo_client"] = client
    return client[current_app.config.get("MONGO_DB_NAME", "content")]


def init_indexes():
    database = get_db()
    database.users.create_index("username", unique=True)
    database.users.create_index("email", unique=True, partialFilterExpression={"email": {"$type": "string", "$gt": ""}})
    database.users.create_index([("provider", 1), ("provider_id", 1)], unique=True)
    database.posts.create_index("slug", unique=True)
    database.posts.create_index([("title", "text"), ("excerpt", "text"), ("body", "text")])
    database.comments.create_index([("post_id", 1), ("created_at", -1)])
