# Analysis import repair

The original analysis selected a different module named score after
importing the historic prompt adapter. It stopped in case encoding
before either fit. Resolve the relation-balance scorer by explicit
file path and pin it in the analysis plan. The collection plan,
prompts, saved token traces, logits, features, keys and optimizer
settings are unchanged. Preserve the original scoring plan.
