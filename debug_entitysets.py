# debug_entitysets.py
from schema_loader import extract_entitysets_from_metadata

if __name__ == "__main__":
    print("\n===== ENTITYSET MAPPING (Dataverse) =====\n")
    mapping = extract_entitysets_from_metadata()
    for logical, entityset in mapping.items():
        print(f"{logical:30} → {entityset}")
