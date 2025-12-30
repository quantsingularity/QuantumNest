# AI Model Usage Examples

## LSTM Price Prediction

```python
import requests
import time

# API endpoint
API_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Submit prediction task
response = requests.post(
    f"{API_URL}/ai/predict/asset/AAPL",
    headers=headers,
    params={
        "days_ahead": 5,
        "model_type": "lstm"
    }
)

task_data = response.json()
task_id = task_data["task_id"]
print(f"Task ID: {task_id}")

# Poll for results
while True:
    response = requests.get(
        f"{API_URL}/ai/tasks/{task_id}",
        headers=headers
    )
    task_status = response.json()

    if task_status["status"] == "SUCCESS":
        predictions = task_status["result"]
        print("Predictions:", predictions)
        break
    elif task_status["status"] == "FAILURE":
        print("Task failed:", task_status.get("error"))
        break

    time.sleep(2)
```

## Sentiment Analysis

```python
# Request sentiment analysis
response = requests.post(
    f"{API_URL}/ai/sentiment/asset/TSLA",
    headers=headers,
    json={"sources": ["news", "twitter", "reddit"]}
)

task_id = response.json()["task_id"]

# Get results
response = requests.get(f"{API_URL}/ai/tasks/{task_id}", headers=headers)
sentiment = response.json()["result"]

print(f"Sentiment Score: {sentiment['overall_score']}")
print(f"Sources Analyzed: {sentiment['sources_count']}")
```

## Portfolio Optimization

```python
# Optimize portfolio
response = requests.post(
    f"{API_URL}/ai/optimize/portfolio/1",
    headers=headers,
    json={
        "risk_tolerance": 0.5,
        "constraints": {
            "max_position": 0.3,
            "min_position": 0.05
        }
    }
)

task_id = response.json()["task_id"]

# Wait for optimization
time.sleep(5)
response = requests.get(f"{API_URL}/ai/tasks/{task_id}", headers=headers)
result = response.json()["result"]

print("Recommended Allocation:")
for asset, weight in result["weights"].items():
    print(f"  {asset}: {weight*100:.2f}%")
```

See [API Reference](../API.md) for more details.
