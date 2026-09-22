#!/usr/bin/env python3
"""
contract_estimate — WAME-methodology minute estimate for the
"Definovať API kontrakt" task.

Defining the contract is real, chargeable work — designing endpoints, request /
response schemas, the data model and the YAML skeleton, then reviewing it — not
free overhead. The size scales with how much surface the contract covers, so the
estimate is derived from the number of endpoints and entities:

    minutes = 45 (base)  +  15 per endpoint  +  15 per entity

The result is always a multiple of 15 and is clamped to the same [60, 480]
window every other task in this skill uses. The three constants below ARE the
estimate — they are not a raw figure waiting for a speedup or a buffer to be
applied on top. See the `## WAME estimate methodology` block in SKILL.md
(`wame-estimate-v2`), which estimates one number directly.

Stdlib only.
"""
from __future__ import annotations

BASE_MINUTES = 45
PER_ENDPOINT = 15
PER_ENTITY = 15
MIN_MINUTES = 60
MAX_MINUTES = 480
STEP = 15


def estimate_minutes(num_endpoints: int, num_entities: int) -> int:
    """Return the contract-task estimate in minutes (multiple of 15, 60..480)."""
    raw = BASE_MINUTES + PER_ENDPOINT * max(0, int(num_endpoints)) \
        + PER_ENTITY * max(0, int(num_entities))
    rounded = round(raw / STEP) * STEP
    return max(MIN_MINUTES, min(MAX_MINUTES, rounded))


def count_contract_surface(contract: dict) -> tuple[int, int]:
    """Count (endpoints, entities) from a structured contract object."""
    spec = contract.get("openapi") or {}
    endpoints = len(spec.get("endpoints") or [])
    entities = len((contract.get("data_model") or {}).get("entities") or [])
    return endpoints, entities


def estimate_from_contract(contract: dict) -> int:
    endpoints, entities = count_contract_surface(contract)
    return estimate_minutes(endpoints, entities)


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--endpoints", type=int, default=0)
    p.add_argument("--entities", type=int, default=0)
    args = p.parse_args()
    print(json.dumps({
        "endpoints": args.endpoints,
        "entities": args.entities,
        "estimated_minutes": estimate_minutes(args.endpoints, args.entities),
    }))
