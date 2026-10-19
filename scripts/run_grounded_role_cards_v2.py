"""Same native runtime and rubric, separately frozen complete-antecedent cards."""
import run_grounded_role_checkpoint as runner

runner.PACK = runner.ROOT / "research/grounded-role-cards-20261019-v2"

if __name__ == "__main__":
    runner.main()
