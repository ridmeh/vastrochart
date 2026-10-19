#!/usr/bin/env python3
"""Downgrade a FastAPI-generated OpenAPI 3.1.0 document to 3.0.3 for Azure
API Management's import validator, which rejects a handful of valid
JSON-Schema-2020-12 constructs OpenAPI 3.1 allows and FastAPI emits:

- exclusiveMinimum/exclusiveMaximum as a NUMBER (3.1) vs a BOOLEAN paired
  with minimum/maximum (3.0) - found empirically: APIM's import rejected
  our real spec with "String was not recognized as a valid Boolean."
- Optional[T] rendered as anyOf: [T, {"type": "null"}] (3.1) vs T +
  nullable: true (3.0, no null type) - 3.0's schema object has no "null"
  type at all, so this would fail the same validator for a different
  reason once the first error was fixed.

Used as a Terraform `external` data source (hashicorp/external) rather
than a one-off script, so the conversion runs against a freshly-fetched
live spec at plan/apply time, not a checked-in file that can drift from
the real app.

Input on stdin: {"url": "<openapi.json url>"} (the `external` data source's
query map). Output on stdout: {"spec": "<converted JSON as a string>"}.
"""

import json
import sys
import urllib.request


def _convert_node(node: object) -> object:
    if isinstance(node, list):
        return [_convert_node(item) for item in node]
    if not isinstance(node, dict):
        return node

    # Optional[T] pattern: anyOf of exactly one real type + {"type": "null"}.
    any_of = node.get("anyOf")
    if isinstance(any_of, list) and len(any_of) >= 2:
        null_branches = [b for b in any_of if b == {"type": "null"}]
        real_branches = [b for b in any_of if b != {"type": "null"}]
        if null_branches and real_branches:
            rest = {k: v for k, v in node.items() if k != "anyOf"}
            if len(real_branches) == 1:
                merged = {**_convert_node(real_branches[0]), **rest, "nullable": True}
            else:
                merged = {
                    "anyOf": [_convert_node(b) for b in real_branches],
                    **rest,
                    "nullable": True,
                }
            return _convert_node(merged)

    converted = {}
    for key, value in node.items():
        if key == "exclusiveMinimum" and isinstance(value, (int, float)):
            converted["minimum"] = value
            converted["exclusiveMinimum"] = True
        elif key == "exclusiveMaximum" and isinstance(value, (int, float)):
            converted["maximum"] = value
            converted["exclusiveMaximum"] = True
        else:
            converted[key] = _convert_node(value)
    return converted


def convert(spec: dict) -> dict:
    result = _convert_node(spec)
    result["openapi"] = "3.0.3"
    return result


def main() -> None:
    query = json.load(sys.stdin)
    with urllib.request.urlopen(query["url"]) as response:
        spec = json.loads(response.read())
    converted = convert(spec)
    json.dump({"spec": json.dumps(converted)}, sys.stdout)


if __name__ == "__main__":
    main()
