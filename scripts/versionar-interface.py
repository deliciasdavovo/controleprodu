"""Keep published HTML asset versions synchronized with their actual contents."""
import hashlib
from pathlib import Path
import re

root = Path(__file__).resolve().parent.parent
index = root / "index.html"
html = index.read_text()
versions = []


def version_asset(match):
    prefix, name, suffix = match.groups()
    asset = (root / name).resolve()
    if not asset.is_relative_to(root) or not asset.is_file():
        raise RuntimeError(f"Arquivo da interface não encontrado: {name}")
    version = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
    versions.append(name + ":" + version)
    return prefix + name + "?v=" + version + suffix


html = re.sub(
    r'((?:src|href)="\./)((?:compiled|styles|src)/[^"?]+\.(?:js|css))(?:\?v=[^"]*)?(\")',
    version_asset,
    html,
)
if not any(name.startswith("compiled/app.js:") for name in versions):
    raise RuntimeError("Script principal não encontrado no HTML")
version = hashlib.sha256("\n".join(versions).encode()).hexdigest()[:12]
html, count = re.subn(
    r'(<meta name="app-version" content=")[^"]+("\s*/>)',
    lambda match: match[1] + "interface-" + version + match[2],
    html,
)
if count != 1:
    raise RuntimeError("Identificação da interface não encontrada no HTML")
index.write_text(html)
print(f"Interface versionada: {version} ({len(versions)} arquivos)")
