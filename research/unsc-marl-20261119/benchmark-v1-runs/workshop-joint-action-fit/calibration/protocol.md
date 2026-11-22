# Retain complete and incomplete branches in joint training

Re-use the sixteen frozen synthetic worlds and their captured language
features. Keep rewards, Adam settings, regularization and the 64-update
budget fixed. Mix one half learned responder probability, one quarter
truthful full disclosure and one quarter withholding. The previous
mixture sent all forced mass to truthful full disclosure. Evaluate with
no forced actions, then with each responder branch fixed. Compare
supported decisions and unwarranted commitments on the eight
fit-excluded UN worlds and the eight archived Syria note pairs.

In the existing environment, a false endorsement yields the same
reward for any chair decision. It is a penalty for the responder, and
contributes zero direct gradient to the chair's predicted action. This
fit adds explicitly incomplete withholding examples. The archived
conflicting notes remain a transfer test. Report their behavior
separately and use the result to decide if visible contradictions
require their own training examples.
