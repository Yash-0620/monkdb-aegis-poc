# Aegis Authorization Test Cases

## Overview

This document describes the authorization cases observed in the Aegis Sidecar logs.

Aegis appears to enforce access based on the requesting identity, requested tool action,
resource context, namespace, business domain, operation type, and other policy attributes.

## Authorization Test Cases

| Case | Requesting Identity | Tool Action | Key Resource / Context | Policy Decision | HTTP Result | Reason | What It Demonstrates |
|---|---|---|---|---|---|---|---|
| 1 | `monkdb-readonly-agent` | `read_enterprise_memory` | Business domain: `Finance` | **PERMIT** | `202 Accepted` | Mathematical bounds verified | Read-only agent is allowed to read Finance enterprise memory |
| 2 | `monkdb-readonly-agent` | `admin_delete_tenant` | Target: `Target API` | **DENY** | `403 Forbidden` | Scope Violation | Read-only agent cannot perform administrative tenant deletion |
| 3 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_A`<br>Domain: `curator@finance.monkdb.com`<br>Operation: `insert`<br>Content: `Q3 Revenue Data`<br>Provenance: `financial_logs` | **PERMIT** | `202 Accepted` | Mathematical bounds verified | Curator is allowed to insert valid Finance data into Plant A |
| 4 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_A`<br>Domain: `curator@hr.monkdb.com`<br>Content: `Employee Salaries`<br>Provenance: `hr_logs` | **DENY** | `422 Unprocessable Entity` | Schema breach: domain does not match `^.+@finance\.monkdb\.com$` | Prevents Finance curator from writing HR-domain data |
| 5 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_B`<br>Domain: `curator@finance.monkdb.com`<br>Content: `Q3 Revenue Data` | **DENY** | `422 Unprocessable Entity` | Schema breach: namespace does not match `^enterprise_memory_plant_A$` | Prevents curator from writing to an unauthorized namespace |
| 6 | `monkdb-readonly-agent` | `write_enterprise_memory` | Target: `Target API` | **DENY** | `403 Forbidden` | Scope Violation | Read-only agent cannot perform write operations |
| 7 | `monkdb-readonly-agent` | `read_enterprise_memory` | Business domain: `Finance` | **PERMIT** | `202 Accepted` | Mathematical bounds verified | Same valid read operation is consistently permitted |
| 8 | `monkdb-readonly-agent` | `admin_delete_tenant` | Target: `Target API` | **DENY** | `403 Forbidden` | Scope Violation | Administrative privilege remains blocked |
| 9 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_A`<br>Domain: `curator@finance.monkdb.com`<br>Content: `Q3 Revenue Data` | **PERMIT** | `202 Accepted` | Mathematical bounds verified | Valid Finance/Plant A write succeeds again |
| 10 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_A`<br>Domain: `curator@hr.monkdb.com`<br>Content: `Employee Salaries` | **DENY** | `422 Unprocessable Entity` | Schema breach | HR-domain write remains blocked |
| 11 | `monkdb-curator-agent` | `write_enterprise_memory` | Namespace: `enterprise_memory_plant_B`<br>Domain: `curator@finance.monkdb.com`<br>Content: `Q3 Revenue Data` | **DENY** | `422 Unprocessable Entity` | Schema breach | Plant B access remains blocked |
| 12 | `monkdb-readonly-agent` | `write_enterprise_memory` | Target: `Target API` | **DENY** | `403 Forbidden` | Scope Violation | Read-only restriction remains enforced |

## Grouped Test Scenarios

The repeated log entries represent five unique security scenarios.

| Test Scenario | Valid/Invalid | Expected Outcome |
|---|---|---|
| Read Finance memory using `monkdb-readonly-agent` | **Valid** | **PERMIT / 202** |
| Write Finance data to `enterprise_memory_plant_A` using `monkdb-curator-agent` | **Valid** | **PERMIT / 202** |
| Attempt HR data write using the Finance curator | **Invalid** | **DENY / 422** |
| Attempt write/delete operations using the readonly agent | **Invalid** | **DENY / 403** |
| Attempt Finance write to `enterprise_memory_plant_B` | **Invalid** | **DENY / 422** |

## Key Security Observations

### Read-only agent

`monkdb-readonly-agent` is permitted to read Finance enterprise memory but is denied write
and administrative delete operations.

### Finance curator

`monkdb-curator-agent` is permitted to write Finance data to
`enterprise_memory_plant_A` when the request satisfies the expected policy constraints.

### Cross-domain protection

A Finance curator cannot submit HR-domain data. The request is rejected because the
business domain does not match the required Finance pattern.

### Namespace isolation

The Finance curator cannot write to `enterprise_memory_plant_B`. The policy restricts
the curator to `enterprise_memory_plant_A`.

### HTTP behavior

- `202 Accepted` corresponds to permitted requests.
- `403 Forbidden` corresponds to scope violations.
- `422 Unprocessable Entity` corresponds to policy/schema validation failures.
- `307 Temporary Redirect` appears to be URL normalization from `/messages` to `/messages/`.

## Conclusion

The logs demonstrate attribute-based authorization in which access is determined by more
than the agent identity alone. The policy considers identity, action, business domain,
namespace, and other request attributes before permitting or denying an operation.