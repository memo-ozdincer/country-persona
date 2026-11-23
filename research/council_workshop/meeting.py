"""Public protocol for a fictional, unanimous clause-negotiation workshop."""
from dataclasses import dataclass, field


def response_schema(**properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


def choice(*options):
    return {"type": "string", "enum": list(options)}


TEXT = {"type": "string"}
FLOOR = response_schema(action=choice("request_floor", "pass"))
SPEECH = response_schema(
    action=choice("ask", "reply", "propose", "accept", "walk_away", "yield_floor"),
    version={"type": "integer"}, text=TEXT,
)
BALLOT = response_schema(vote=choice("yes", "no", "abstain"), version={"type": "integer"}, reason=TEXT)
DRAFT = response_schema(text=TEXT, reason=TEXT)


@dataclass
class Meeting:
    countries: list[str]
    draft: str
    version: int = 1
    accepted: list[str] = field(default_factory=list)
    queue: list[str] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    status: str = "open"

    def view(self):
        return dict(draft=self.draft, version=self.version, accepted=self.accepted.copy(),
                    queue=self.queue.copy(), history=self.history.copy())

    def apply(self, country, action):
        name, version, text = action["action"], action["version"], action["text"].strip()
        if type(version) is not int or version != self.version:
            raise ValueError(f"{country} acted on stale or invalid draft {version}")
        if not text or len(text.split()) > 120:
            raise ValueError(f"{country} must supply 1–120 words")
        if name == "propose":
            if text == self.draft:
                raise ValueError("A revision must change the wording")
            self.version += 1
            self.draft = text
            self.accepted.clear()
        elif name == "accept":
            if country not in self.accepted:
                self.accepted.append(country)
            if len(self.accepted) == len(self.countries):
                self.status = "unanimous_acceptance"
        elif name == "walk_away":
            self.status = "walkout"
        elif name not in ("ask", "reply", "yield_floor"):
            raise ValueError(f"Unknown action: {name}")
        self.history.append(dict(country=country, action=name, version=version,
                                 resulting_version=self.version, text=text))


def run_meeting(case, countries, turn_cap, decide, collect_votes=False, call_cap=None):
    """decide(country, instruction, public_state, schema) returns a structured action."""
    ballot_count = len(countries) if collect_votes else 0
    discussion_cap = call_cap - ballot_count if call_cap is not None else None
    if discussion_cap is not None and discussion_cap < 1:
        raise ValueError("Call cap must cover the opening speech and all requested ballots")

    calls = 0

    def ask(country, instruction, public, schema):
        nonlocal calls
        calls += 1
        return decide(country, instruction, public, schema)

    meeting = Meeting(countries, case["draft"])
    speaker = countries[0]
    for turn in range(1, turn_cap + 1):
        action = ask(speaker, SPEAK_INSTRUCTION, meeting.view(), SPEECH)
        meeting.apply(speaker, action)
        if meeting.status != "open":
            break
        if turn == turn_cap:
            meeting.status = "turn_cap"
            break

        # Existing requests retain priority. New ties start after the last speaker.
        start = countries.index(speaker) + 1
        poll_order = [country for country in countries[start:] + countries[:start]
                      if country not in meeting.queue]
        if discussion_cap is not None and calls + len(poll_order) > discussion_cap:
            meeting.status = "call_cap"
            break
        public = meeting.view()
        for country in poll_order:
            request = ask(country, FLOOR_INSTRUCTION, public, FLOOR)["action"]
            if request == "request_floor":
                meeting.queue.append(country)
            elif request != "pass":
                raise ValueError(f"Unknown floor request: {request}")
        if not meeting.queue:
            meeting.status = "all_passed"
            break
        if discussion_cap is not None and calls == discussion_cap:
            meeting.status = "call_cap"
            break
        speaker = meeting.queue.pop(0)

    # These are advisory ballots. All voters see the same pre-ballot state.
    ballots = {}
    if collect_votes:
        for country in countries:
            ballot = ask(country, VOTE_INSTRUCTION, meeting.view(), BALLOT)
            if type(ballot["version"]) is not int or ballot["version"] != meeting.version:
                raise ValueError(f"{country} voted on the wrong version")
            if ballot["vote"] not in ("yes", "no", "abstain") or not ballot["reason"].strip():
                raise ValueError(f"Invalid ballot from {country}")
            ballots[country] = ballot
    result = dict(**meeting.view(), status=meeting.status, ballots=ballots)
    if call_cap is not None:
        result["calls"] = calls
    return result


SPEAK_INSTRUCTION = """You have the floor. Choose one action. Use the CURRENT version for every
action. propose replaces the clause with your exact text and clears every acceptance, including
your own. accept explicitly accepts that exact version. ask and reply are public remarks.
walk_away ends this unanimous workshop. yield_floor gives up this turn. For propose use text
only for the clause; otherwise use it for your question, reply or reason. Use 1–120 words."""
FLOOR_INSTRUCTION = """Request the floor if you have a question, reply, edit or decision to make.
Pass if you have nothing to add. All newly polled delegates see the same public state."""
VOTE_INSTRUCTION = """Cast a private advisory vote on the current version and give one brief reason.
This records your position separately from public acceptance. It is a workshop vote."""
