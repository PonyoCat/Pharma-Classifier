# tools/make_deploy_zip.py
import zipfile, pathlib, sys

root = pathlib.Path(__file__).resolve().parents[1]  # repo-rod
want = [
    "backend",              # ← skift til "app" hvis dit backend-kode ligger dér
    ".platform",
    "Procfile",
    "requirements.txt",
    "frontend/dist",
]

def add(z, p):
    p = root / p
    if not p.exists():
        print(f"ADVARSEL: mangler {p}")
        return
    if p.is_file():
        z.write(p, p.as_posix())
    else:
        for f in p.rglob("*"):
            if f.is_file():
                z.write(f, (root / f).relative_to(root).as_posix())

out = root / "deploy.zip"
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for p in want:
        add(z, p)

with zipfile.ZipFile(out) as z:
    assert "frontend/dist/index.html" in z.namelist(), "frontend/dist mangler i ZIP!"
print(f"Lavet: {out}")
