"""Use the already pinned native runner for the separately frozen quote cards."""
import run_grounded_role_checkpoint as runner

runner.PACK = runner.ROOT / "research/grounded-role-cards-20261019-v1"

if __name__ == "__main__":
    runner.main()
