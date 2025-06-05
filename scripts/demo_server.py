#!/usr/bin/env python3
import json
import sys
from fastapi import FastAPI

# Read JSON file once at startup
if len(sys.argv) < 2:
    print("Usage: python main.py <url_path>")
    sys.exit(1)

json_file_path = 'response.json'
with open(json_file_path, 'r') as file:
    cached_data = json.load(file)

app = FastAPI()

@app.get(f"{sys.argv[1]}")
def get_data():
    """Serve cached JSON data"""
    return cached_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
