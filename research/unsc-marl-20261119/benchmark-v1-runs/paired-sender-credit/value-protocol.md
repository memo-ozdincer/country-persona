# Fit separate delivery values from paired experience

The exact-gradient diagnostic still misses Belgium sends on the training
grid. Replace policy-gradient updating of the sender with an empirical
model of the score increment from a delivered message. The two values
per private view correspond to whether the reply is delivered. Fit both
from paired simulated rewards with common channel and receiver randomness.
Subtract attempted sending cost analytically. The operational sender needs
only its private view, channel estimates and price, plus the fitted weights.

Keep both actors updating together. The reply actor uses the previous
sampled shared-reward update, driven by the new sender's exploration.
The sender draws from a sigmoid with fixed temperature 2 utility points.
Use running means of delivered score differences and initialize both
gains to zero. Use no oracle outcomes outside these paired comparisons.
Keep the original seed, 512 updates, batch 256, held grid and terminal
score budget. Report exact oracle regret and both learned actor weights.
