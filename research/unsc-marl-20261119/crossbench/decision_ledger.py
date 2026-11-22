"""Read a workshop decision from explicitly disclosed constraints and provenance."""


def readout(options, roles, messages):
    """Return only the agreement or impasse facts supported by the public log."""
    options, roles = tuple(options), tuple(roles)
    if (not options or len(roles) != 2 or not all(isinstance(x, str) and x.strip() for x in (*options, *roles))
            or len(set(options)) != len(options) or len(set(roles)) != 2):
        raise ValueError("Expected a nonempty unique option menu and two distinct roles")
    by_role = {role: {option: {} for option in options} for role in roles}
    seen = set()
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("A disclosure must be an object")
        id_, role = message.get("id"), message.get("role")
        if (not isinstance(id_, str) or not id_.strip() or id_ in seen
                or not isinstance(role, str) or role not in by_role):
            raise ValueError("A disclosure needs a unique ID and a known role")
        seen.add(id_)
        for field in ("accepts", "excludes"):
            claimed = message.get(field, [])
            if (not isinstance(claimed, list) or not all(isinstance(o, str) and o in options for o in claimed)
                    or len(set(claimed)) != len(claimed)):
                raise ValueError(f"Invalid {field} list in {id_}")
            for option in claimed:
                by_role[role][option].setdefault(field, []).append(id_)

    conflicts, verified, blocked, unresolved = [], {}, {}, []
    for option in options:
        rows = {role: by_role[role][option] for role in roles}
        for role, signs in rows.items():
            if len(signs) == 2:
                conflicts.append({"option": option, "role": role, **signs})
        if all("accepts" in rows[role] for role in roles):
            verified[option] = {role: rows[role]["accepts"] for role in roles}
        elif any("excludes" in rows[role] for role in roles):
            blocked[option] = {role: rows[role]["excludes"] for role in roles if "excludes" in rows[role]}
        else:
            unresolved.append(option)
    if conflicts:
        # Keep raw evidence and abstain from a terminal certificate until a
        # participant's incompatible declarations are resolved.
        return {"state": "CONTRADICTORY_DISCLOSURE", "conflicts": conflicts}
    state = "AGREEMENT_POSSIBLE" if verified else "IMPASSE" if not unresolved else "UNRESOLVED"
    return {"state": state, "verified_options": verified, "blocked_options": blocked,
            "unresolved_options": unresolved, "unique_verified": len(verified) == 1 and not unresolved}


def truthful_disclosure(message, private_menu):
    """Environment-side audit. The writer's readout never receives private_menu."""
    return (set(message.get("accepts", [])) <= set(private_menu)
            and not set(message.get("excludes", [])) & set(private_menu))
