# Ranked-object format replay

The strict actor contract expected a JSON array of strings. The UK
call returned ordered objects with IDs and integer ranks. Preserve the
strict run and the raw response. For the additional format replay,
accept an object list only if every object has exactly the two stated
fields and the rank equals its one-based position. Pass the resulting
ID list through the original role membership and duplicate checks.
Absent, ambiguous, duplicated or unknown IDs are not repaired. No
model call or editorial passage selection is added. This parser control
was specified after inspecting the raw format.
