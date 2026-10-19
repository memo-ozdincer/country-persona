"""Frozen writer-map inputs with a smaller requested word target."""
import run_grounded_role_checkpoint as runner

runner.PACK = runner.ROOT / "research/grounded-role-budget-20261019-v1"

if __name__ == "__main__":
    runner.main()
