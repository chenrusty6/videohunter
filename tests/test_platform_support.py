import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core import platform_support as desktop
from core import clipboard


class NativeOperationsTests(unittest.TestCase):
    def test_mac_clipboard_preserves_unicode_and_does_not_use_a_shell(self):
        with patch.object(desktop.subprocess, 'run') as call:
            call.return_value = subprocess.CompletedProcess([], 0, 'https://example.test/影片\n', '')
            self.assertEqual(desktop.mac_clipboard(), 'https://example.test/影片\n')
            self.assertEqual(call.call_args.args[0], ['/usr/bin/pbpaste'])
            self.assertFalse(call.call_args.kwargs.get('shell', False))

    def test_folder_name_and_notification_are_applescript_arguments(self):
        payload = '引號 " & do shell script "touch /tmp/unwanted"'
        with patch.object(desktop.subprocess, 'run') as call:
            call.return_value = subprocess.CompletedProcess([], 0, '/Users/test/影片\n', '')
            self.assertEqual(desktop.mac_choose_folder(payload), '/Users/test/影片')
            command = call.call_args.args[0]
            self.assertEqual(command[-1], payload)
            self.assertNotIn(payload, command[2])
            desktop.mac_notification(payload, payload)
            command = call.call_args.args[0]
            self.assertEqual(command[-2:], [payload, payload])
            self.assertNotIn(payload, command[2])

    def test_clipboard_permission_failure_does_not_crash(self):
        with patch.object(desktop.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'pbpaste')):
            self.assertEqual(desktop.mac_clipboard(), '')

    def test_mac_clipboard_url_routes_to_native_adapter(self):
        with patch.object(clipboard.sys, 'platform', 'darwin'), patch.object(clipboard, 'mac_clipboard', return_value='copied: https://example.test/video'):
            self.assertEqual(clipboard.extract_url_from_clipboard(), 'https://example.test/video')

    def test_bundled_ffmpeg_has_priority_over_host_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / 'bin/ffmpeg'
            binary.parent.mkdir()
            binary.touch()
            with patch.object(desktop, 'RESOURCE_DIR', Path(temp)), patch.object(desktop, 'PLATFORM', 'darwin'):
                self.assertEqual(desktop.ffmpeg_directory(), str(binary.parent))

    def test_finder_path_with_shell_characters_remains_one_argument(self):
        folder = '/Users/test/影片 $(touch nope)'
        with patch.object(desktop, 'PLATFORM', 'darwin'), patch.object(desktop.subprocess, 'run') as call:
            desktop.open_folder(folder)
            self.assertEqual(call.call_args.args[0], ['/usr/bin/open', folder])
            self.assertFalse(call.call_args.kwargs.get('shell', False))


if __name__ == '__main__':
    unittest.main()
