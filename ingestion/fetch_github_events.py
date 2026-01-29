
import requests
import os
import json
from datetime import datetime

url = "https://api.github.com/events"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    events = response.json()

    base_path = "/Volumes/workspace/default/raw_github_events"
    date_path = datetime.utcnow().strftime("date=%Y-%m-%d")

    full_dir = os.path.join(base_path, date_path)
    os.makedirs(full_dir, exist_ok=True)

    file_name = datetime.utcnow().strftime("events_%H%M%S.json")
    file_path = os.path.join(full_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

    print(f"Saved {len(events)} events to {file_path}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching events: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("GitHub").getOrCreate()

df_raw = spark.read.option('columnNameOfCorruptRecord','_corrupt_record').option("multiline",'true').option("mergeSchema", "true").format("json").load("/Volumes/workspace/default/raw_github_events/")

display(df_raw)
