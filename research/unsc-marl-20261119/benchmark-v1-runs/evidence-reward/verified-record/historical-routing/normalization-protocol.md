# Normalize the exact echoed desk envelope

All three native responses copied the requested sentences exactly and
returned an outer object containing the desk and evidence map. The
frozen flat parser admitted zero. Preserve that failure. A separate
adapter accepts this outer key set only when the named desk matches
the addressed role and the evidence value is a mapping. It then
applies the original key and full source-text check to the contents.
Test wrong desk and wrong envelope type. Reuse the original native
generation. This is an adaptive format repair with no extra calls.
