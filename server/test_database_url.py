"""Regression checks for socket URLs and reserved credential characters."""
import configparser
import importlib.util
import os
import pathlib
import unittest
from unittest.mock import patch

from sqlalchemy.engine import make_url

spec = importlib.util.spec_from_file_location("mem0_server_db", pathlib.Path(__file__).with_name("db.py"))
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)


class DatabaseUrlTests(unittest.TestCase):
    def test_socket_peer_without_password(self):
        with patch.dict(os.environ, {"POSTGRES_HOST": "/var/run/postgresql", "POSTGRES_USER": "service"}, clear=True):
            result = make_url(db._build_database_url())
        self.assertIsNone(result.host)
        self.assertIsNone(result.password)
        self.assertEqual(result.query["host"], "/var/run/postgresql")
        self.assertEqual(result.query["port"], "5432")

    def test_tcp_credentials_round_trip_and_alembic_interpolation(self):
        with patch.dict(os.environ, {"POSTGRES_HOST": "localhost", "POSTGRES_PASSWORD": "p@:/%?#", "POSTGRES_USER": "a:b"}, clear=True):
            raw = db._build_database_url()
        result = make_url(raw)
        self.assertEqual(result.password, "p@:/%?#")
        self.assertEqual(result.username, "a:b")
        parser = configparser.ConfigParser()
        parser.add_section("alembic")
        parser.set("alembic", "sqlalchemy.url", raw.replace("%", "%%"))
        self.assertEqual(parser.get("alembic", "sqlalchemy.url"), raw)


if __name__ == "__main__":
    unittest.main()
