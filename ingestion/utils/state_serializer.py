import os
import pickle  


def save_state(state):
    file_basename = state["file_basename"]
    state_file_path = state["file_paths"]["processed_dir"] / file_basename
    with open(f"{state_file_path}.pkl", "wb") as f:
        pickle.dump(state, f)

def load_state(filepath):
    with open(filepath, "rb") as f:
        return pickle.load(f)