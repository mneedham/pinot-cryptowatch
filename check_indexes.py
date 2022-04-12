import requests
import csv
import pandas as pd

pinot_url = "http://localhost:9000"
table_name = "trades"

response = requests.get(f"{pinot_url}/schemas/{table_name}")
r = response.json()

fields = r.get("dimensionFieldSpecs", []) + r.get("dateTimeFieldSpecs", []) + r.get("metricFieldSpecs", [])
columns = [field["name"] for field in fields]

data = { "columns": columns}
response = requests.get(f"{pinot_url}/segments/{table_name}_REALTIME/metadata", params=data)

r = response.json()
segments = list(r.items())
segments.sort(key=lambda x: x[0])

for segment, values in segments:
    print(segment)
    columns = ["column", "sorted"] + list(list(values["indexes"].values())[0].keys())
    rows = []
    for column in values.get("columns", []):
        column_name = column["fieldSpec"]["name"]
        filtered_map = {k:v for k,v in values["indexes"].items() if k == column_name}
        row = [column_name, column["sorted"]] + list(filtered_map[column_name].values())
        rows.append(row)

    new_df = pd.DataFrame(columns=columns, data=rows)
    print(new_df)