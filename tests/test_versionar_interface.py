import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/versionar-interface.py"


class PublishedAssetVersionsTest(unittest.TestCase):
    def test_versions_change_with_assets_and_stay_stable_on_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "compiled").mkdir()
            (root / "styles").mkdir()
            shutil.copy(SCRIPT, root / "scripts/versionar-interface.py")
            app = root / "compiled/app.js"
            app.write_text("console.log('primeira versão')")
            css = root / "styles/main.css"
            css.write_text("body{color:green}")
            index = root / "index.html"
            index.write_text('<meta name="app-version" content="antiga" />'
                             '<script src="./compiled/app.js?v=antiga"></script>'
                             '<link href="./styles/main.css?v=antiga">')
            def run():
                subprocess.run(["python3", str(root / "scripts/versionar-interface.py")],
                               check=True, capture_output=True)
                return index.read_text()
            first = run()
            self.assertNotIn("antiga", first)
            self.assertEqual(first, run())
            app.write_text("console.log('segunda versão')")
            second = run()
            self.assertNotEqual(first, second)
            self.assertIn(hashlib.sha256(app.read_bytes()).hexdigest()[:12], second)
            unchanged_css_version = hashlib.sha256(css.read_bytes()).hexdigest()[:12]
            self.assertIn(unchanged_css_version, first)
            self.assertIn(unchanged_css_version, second)
            self.assertEqual(second, run())


if __name__ == "__main__":
    unittest.main()
