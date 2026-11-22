The retained collector completed all four model calls and sealed their
prompts and token traces. Its legacy CPU verification branch raised a
RecursionError because the patched request builder called itself.
The launch and model outputs are unchanged. The standalone CPU
verifier checks the sealed manifest, exact baseline prompt delta,
native template tokenization, token limits, stop token and decoded
text from the saved traces. Its receipt records four verified calls.
