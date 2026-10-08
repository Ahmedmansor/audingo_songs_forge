import sys, os
sys.path.insert(0, os.path.abspath("."))

# Test imports
import db
import scripts.lyrics_graph as lg
import presentation.tabs.tab3_refinement as t3

print("Imports successful!")

# Test save and load refinement state with concept
db.save_refinement_state("test lyrics", {"overall_score": 92}, "Two friends meet at a diner.")
loaded = db.load_refinement_state()
assert loaded.get("concept") == "Two friends meet at a diner.", f"Failed concept persistence: {loaded}"
print("DB refinement state with concept verified OK!")
