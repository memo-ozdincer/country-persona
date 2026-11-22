# Robust replay preparation error

The first robust replays stopped at the nominal reference comparison.
The in-memory policy choices contain tuples, which the frozen JSON
serializes as lists. The corrected comparison applies the artifact's
JSON representation before asserting complete equality. The arms,
forecasts and optimizer are kept as specified by the initial protocol.
No corrected held comparison was emitted during the stopped attempts.
