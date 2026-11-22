# Replay equivalent numeric passage IDs

The China call returned a JSON list of integers. The strict run and
the predeclared ranked-object parser both reject this format. Preserve
that result. As a post hoc parser ablation, convert a nonempty homogeneous
array of exact integers into decimal strings, then apply the original
role-membership and duplicate checks. Booleans, reals, mixed types and
foreign IDs remain invalid. Preserve order. The ablation changes no
selector, prompt, speaker text, calibration order, or reward mark.
