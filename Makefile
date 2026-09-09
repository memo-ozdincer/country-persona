.PHONY: setup test normalize prepare audit inventory
setup:
	uv sync --locked --extra data --extra dev
test:
	uv run pytest -q
normalize:
	uv run persona normalize
prepare:
	uv run persona build
audit:
	uv run persona audit data/prepared/pilot/pilot.canonical.jsonl --verify-raw --output reports/pilot_audit.json
inventory:
	uv run persona inventory
