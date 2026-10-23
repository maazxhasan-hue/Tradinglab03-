import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.nexora_drive_backup import DriveBackupError, _config, restore_backup


class DriveBackupSafetyTests(unittest.TestCase):
    def test_missing_oauth_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(DriveBackupError, "not configured"):
                _config()

    def test_restore_rejects_invalid_file_id_before_network_access(self):
        with self.assertRaisesRegex(DriveBackupError, "Invalid Drive file ID"):
            restore_backup("../bad", "/tmp/unused-nexora-db")

    def test_restore_rejects_unknown_backup_when_drive_is_configured(self):
        env = {
            "GOOGLE_DRIVE_CLIENT_ID": "client",
            "GOOGLE_DRIVE_CLIENT_SECRET": "secret",
            "GOOGLE_DRIVE_REFRESH_TOKEN": "refresh",
            "GOOGLE_DRIVE_FOLDER_ID": "folder",
        }
        with patch.dict(os.environ, env, clear=True), \
             patch("company.nexora_drive_backup._access_token", return_value="token"), \
             patch("company.nexora_drive_backup.list_backups", return_value=[]):
            with self.assertRaisesRegex(DriveBackupError, "not a listed Nexora HQ backup"):
                restore_backup("file123", "/tmp/unused-nexora-db")


if __name__ == "__main__":
    unittest.main()
