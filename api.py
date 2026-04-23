from fastapi import FastAPI
import json

app = FastAPI()

with open("output/scraped_data.json") as f:
    data = json.load(f)

@app.get("/top")
def get_top():
    return sorted(data, key=lambda x: x.get("trust_score", 0), reverse=True)[:5]
