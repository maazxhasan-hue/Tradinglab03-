import unittest
from company.database import _adapt_sql, database_target, is_postgres_target

class DatabaseCompatibilityTests(unittest.TestCase):
    def test_sqlite_target_remains_local_without_database_url(self):
        self.assertFalse(is_postgres_target("data/app.sqlite3"))

    def test_postgres_url_is_detected(self):
        self.assertTrue(is_postgres_target("postgresql://user:pass@host/db"))
        self.assertTrue(is_postgres_target("postgres://user:pass@host/db"))

    def test_sqlite_pragmas_are_ignored_for_postgres(self):
        self.assertIsNone(_adapt_sql("PRAGMA foreign_keys=ON"))
        self.assertIsNone(_adapt_sql("PRAGMA journal_mode=WAL;"))

    def test_positional_placeholders_are_adapted(self):
        self.assertEqual(_adapt_sql("SELECT * FROM tasks WHERE task_id=?"), "SELECT * FROM tasks WHERE task_id=%s")

    def test_insert_or_ignore_is_conflict_safe(self):
        sql = _adapt_sql("INSERT OR IGNORE INTO service_prices(service_id,name,price) VALUES(?,?,?)")
        self.assertEqual(sql, "INSERT INTO service_prices(service_id,name,price) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING")

if __name__ == "__main__":
    unittest.main()
