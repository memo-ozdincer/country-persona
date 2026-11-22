# Component replay import repair

The first component replay stopped before scoring because its
generic module name collided with an earlier archived experiment's
import. Load this case's transfer module under a distinct name.
The locked transfer run and its policies reproduce unchanged.

The second attempt reached the export and encountered a NumPy integer
in a summary count. Convert the probability-weighted reward to a
Python float at the evaluator boundary. Both stopped attempts left
no score artifact, and neither repair changes the policy comparison.
