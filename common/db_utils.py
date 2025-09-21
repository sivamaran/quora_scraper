from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ---------------- Load Schema Template ----------------
_schema_path = Path(__file__).resolve().parent / "schema_template.json"
with open(_schema_path, "r", encoding="utf-8") as f:
    SCHEMA = json.load(f)


# ---------------- MongoDB Save ----------------
def save_to_mongo(json_list, db_name="leadgen", collection_name="quora_leads"):
    """Insert a list of schema-mapped dicts into MongoDB."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    if json_list:
        result = collection.insert_many(json_list)
        print(f"✅ Saved {len(result.inserted_ids)} records into MongoDB: {db_name}.{collection_name}")
    else:
        print("⚠️ No records to save")


# ---------------- JSON Save ----------------
def save_to_json(json_list, output_file="quora_output.json"):
    """Write a list of schema-mapped dicts into a JSON file."""
    if not json_list:
        print("⚠️ No records to save")
        return

    # Strip MongoDB _id if present
    clean_list = []
    for item in json_list:
        if "_id" in item:
            item = dict(item)  # make a shallow copy
            item.pop("_id")
        clean_list.append(item)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_list, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(clean_list)} records into JSON file: {output_file}")
