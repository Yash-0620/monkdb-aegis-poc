import requests
import json
import time

# --- CONFIGURATION ---
CONTROL_PLANE_URL = "https://aegis-live-node.onrender.com"
SIDECAR_URL = "http://127.0.0.1:8080/messages" 

# TO DO: Paste your two active keys here!
READONLY_API_KEY = "aegis_live_a0fb22acea181c677f3983f70e150456" 
CURATOR_API_KEY = "aegis_live_8f337789b6ba9d9a7073afd5c5c5d15a"

def mint_token(api_key, agent_name):
    res = requests.post(f"{CONTROL_PLANE_URL}/mint", json={"api_key": api_key})
    return res.json().get("token")

def fire_payload(token, tool_name, args):
    headers = {"X-Aegis-IBCT": token, "Content-Type": "application/json"}
    payload = {"method": "tools/call", "params": {"name": tool_name, "arguments": args}}
    
    start_time = time.time()
    res = requests.post(SIDECAR_URL, json=payload, headers=headers)
    res.latency_ms = (time.time() - start_time) * 1000 
    return res

# 1. Establish Identities
readonly_token = mint_token(READONLY_API_KEY, "Read-Only Agent")
curator_token = mint_token(CURATOR_API_KEY, "Curator Agent")

print("\n--- SCENARIO 1: TOOL AUTHORIZATION ---")
res1 = fire_payload(readonly_token, "read_enterprise_memory", {"business_domain": "Finance"})
print(f"[1A] PERMIT MEMORY RETRIEVAL (Expected: 200/202) -> Status: {res1.status_code} in {res1.latency_ms:.2f}ms")

res2 = fire_payload(readonly_token, "admin_delete_tenant", {"tenant_id": "plant_A"})
print(f"[1B] BLOCK ADMIN OPERATION (Expected: 401/403) -> Status: {res2.status_code} | Reason: {res2.json().get('reason', 'Scope Violation')} in {res2.latency_ms:.2f}ms")


print("\n--- SCENARIO 2: CONTEXT/RESOURCE AUTHORIZATION ---")
res3 = fire_payload(curator_token, "write_enterprise_memory", {
    "target_namespace": "enterprise_memory_plant_A",
    "business_domain": "curator@finance.monkdb.com", 
    "calling_identity": "curator_bot_01",
    "operation_type": "insert",
    "content_object": "Q3 Revenue Data",
    "provenance_context": "financial_logs"
})
print(f"[2A] ALLOW AUTHORIZED DOMAIN & NAMESPACE (Expected: 200/202) -> Status: {res3.status_code} in {res3.latency_ms:.2f}ms")

res4 = fire_payload(curator_token, "write_enterprise_memory", {
    "target_namespace": "enterprise_memory_plant_A",
    "business_domain": "curator@hr.monkdb.com", # <--- UNAUTHORIZED EMAIL DOMAIN
    "calling_identity": "curator_bot_01",
    "operation_type": "insert",
    "content_object": "Employee Salaries",
    "provenance_context": "hr_logs"
})
print(f"[2B] BLOCK UNAUTHORIZED DOMAIN (Expected: 422) -> Status: {res4.status_code} | Reason: {res4.json().get('validation_error', 'Schema Breach')} in {res4.latency_ms:.2f}ms")

res5 = fire_payload(curator_token, "write_enterprise_memory", {
    "target_namespace": "enterprise_memory_plant_B", # <--- UNAUTHORIZED NAMESPACE
    "business_domain": "curator@finance.monkdb.com", # <--- VALID EMAIL DOMAIN
    "calling_identity": "curator_bot_01",
    "operation_type": "insert",
    "content_object": "Q3 Revenue Data",
    "provenance_context": "financial_logs"
})
print(f"[2C] BLOCK UNAUTHORIZED NAMESPACE (Expected: 422) -> Status: {res5.status_code} | Reason: {res5.json().get('validation_error', 'Schema Breach')} in {res5.latency_ms:.2f}ms")


print("\n--- SCENARIO 3: GOVERNED MEMORY WRITES ---")
res6 = fire_payload(readonly_token, "write_enterprise_memory", {
    "target_namespace": "enterprise_memory_plant_A",
    "business_domain": "curator@finance.monkdb.com",
    "calling_identity": "rogue_bot",
    "operation_type": "insert",
    "content_object": "Fake Data",
    "provenance_context": "hallucination"
})
print(f"[3] BLOCK UNAUTHORIZED WRITER (Expected: 401/403) -> Status: {res6.status_code} | Reason: {res6.json().get('reason', 'Scope Violation')} in {res6.latency_ms:.2f}ms")