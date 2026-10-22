import requests

headers = {
    "Authorization": "Bearer token-alice-demo-secret-123",
    "Content-Type": "application/json"
}

# 1. Create conversation
conv = requests.post("http://localhost:8000/api/v1/conversations", headers=headers, json={"title": "Verification"}).json()
cid = conv["id"]
print(f"Created conversation: {cid}")

# 2. Ask question
res = requests.post(
    f"http://localhost:8000/api/v1/conversations/{cid}/messages",
    headers=headers,
    json={"content": "Gambarkan grafik batang perbandingan On-Time Rate antar carrier di bulan Agustus 2026"}
).json()

print("\n--- AI AGENT ANSWER ---")
print(res.get("answer"))
print("\n--- DATA BASIS ---")
print(res.get("data_basis"))
print("\n--- OUTCOME ---")
print(res.get("outcome"))
