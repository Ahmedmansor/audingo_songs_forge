"""
setup_folders.py — Run once to create the required project directories
and placeholder files so they appear in the file explorer.
"""
from pathlib import Path

BASE = Path(__file__).parent.resolve()

folders = [
    BASE / "Upload_Queue",
    BASE / "Uploaded_Done",
    BASE / "logs",
    BASE / "Upload_Queue" / "Ep_01",   # sample episode structure
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)
    # Drop a .gitkeep so the folder shows up in git and the sidebar
    keeper = folder / ".gitkeep"
    if not keeper.exists():
        keeper.touch()

print("✓ Folders created:")
for f in folders:
    print(f"    {f}")
