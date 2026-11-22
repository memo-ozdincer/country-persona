# Preparation receipt

The first launch stopped before opening a run directory. The prompt
builder returned tuple keys and option orders. Loading the JSON plan
returned lists, so the plan equality check failed. The collector now
constructs lists before serialization. The repaired plan reproduces
all initial request bytes after JSON serialization. The code hash
is the only changed plan field. Neither attempt changed the fit or
any claim, witness, label, option order, or model setting.
