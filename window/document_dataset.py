"""Frozen controlled document: annotations are supplied, not extracted by an LLM."""
import copy

PARAGRAPHS = {
    "S1": "The Atlas field programme assigns its primary work to team Cedar. This group handles planning, incident review and the preparation of weekly reports. Its assignment concerns responsibility for the programme, rather than the location where documents are stored. Temporary visitors do not change the assignment.",
    "S2": "Team Cedar is led by Mira. The lead checks reports before the weekly meeting and coordinates requests received from other groups. Assistants can prepare drafts, but they do not inherit the leadership role. This paragraph records the current lead for the present version of the programme handbook.",
    "S3": "Atlas also maintains an independent responsibility route through team Birch. This secondary team can provide the programme contact when the primary directory is unavailable. The two directories are kept separately for this exercise. A missing entry in one directory does not erase entries that remain in the other.",
    "S4": "Team Birch is led by Mira. Its records identify the same programme contact through the secondary responsibility route. The team handles continuity checks and records any disagreement between directories. If the two current directories identify different leads, the handbook does not authorize choosing one merely because it appears first.",
    "S5": "Mira works at the Porto office. This is the office associated with the person, not the storage site associated with a project. Travel schedules and remote meetings are outside the scope of this handbook. Questions about the programme lead's office therefore require identifying the lead before locating that person's office.",
    "S6": "Atlas uses Vega as its backup repository. The repository receives copies of approved material after review. It is a named storage service and should not be confused with a team or a person. This handbook does not specify the price of that service or the total budget of Atlas.",
    "S7": "The Vega repository stores its material in Lima. Copies are indexed by project name and document version. Routine indexing does not establish a new programme leader. This location describes stored material only; it gives no evidence about the office of a coordinator or the address of a meeting.",
    "S8": "The separate Orion programme belongs to team Maple. Its schedules and materials are managed independently from Atlas. Similar reporting routines do not imply a shared leader. A question about Orion must follow its own responsibility route, even when most of the surrounding handbook discusses the Atlas programme.",
    "S9": "Team Maple is led by Nora. The current directory assigns review and coordination duties to that person. Historical meeting guests are not listed as alternative leads. Nothing in this entry changes either of the Atlas directories. Names must remain attached to their stated teams when answering questions across programmes.",
    "S10": "Nora works at the Recife office. The office entry is included to distinguish the two people mentioned in this handbook. It is unrelated to the Vega storage location. When a requested fact is absent or when current routes disagree, the appropriate answer for this exercise is UNKNOWN, rather than a guess."
}
FACTS = {"S1": ("Atlas", "team", "Cedar"), "S2": ("Cedar", "lead", "Mira"),
         "S3": ("Atlas", "team", "Birch"), "S4": ("Birch", "lead", "Mira"),
         "S5": ("Mira", "office", "Porto"), "S6": ("Atlas", "backup", "Vega"),
         "S7": ("Vega", "storage", "Lima"), "S8": ("Orion", "team", "Maple"),
         "S9": ("Maple", "lead", "Nora"), "S10": ("Nora", "office", "Recife")}


def dataset():
    specifications = [
        ("lead", "Who leads Atlas?", "Atlas", ["team", "lead"], [["S1", "S2"], ["S3", "S4"]], "Mira", []),
        ("office", "In which office does the lead of Atlas work?", "Atlas", ["team", "lead", "office"], [["S1", "S2", "S5"], ["S3", "S4", "S5"]], "Porto", []),
        ("storage", "Where is the backup repository of Atlas located?", "Atlas", ["backup", "storage"], [["S6", "S7"]], "Lima", []),
        ("orion", "Who leads Orion?", "Orion", ["team", "lead"], [["S8", "S9"]], "Nora", []),
        ("budget", "What is the budget of Atlas?", "Atlas", ["budget"], [[]], "UNKNOWN", []),
        ("lost_a", "Who leads Atlas?", "Atlas", ["team", "lead"], [["S1", "S2"], ["S3", "S4"]], "Mira", ["S1", "S2"]),
        ("lost_essential", "Who leads Atlas?", "Atlas", ["team", "lead"], [["S1", "S2"], ["S3", "S4"]], "UNKNOWN", ["S2", "S4", "S5"]),
        ("conflict", "Who leads Atlas?", "Atlas", ["team", "lead"], [["S1", "S2"], ["S3", "S4"]], "UNKNOWN", []),
    ]
    cases = []
    for name, question, entity, relations, paths, expected, removed in specifications:
        sections = {k: v for k, v in PARAGRAPHS.items() if k not in removed}
        facts = copy.deepcopy(FACTS)
        if name == "conflict":
            sections["S4"] = sections["S4"].replace("led by Mira", "led by Nora").replace("the same programme contact", "a different programme contact")
            facts["S4"] = ("Birch", "lead", "Nora")
        routes = []
        for path in paths:
            sources = [{"id": sid, "context": "document", "revision": 1,
                        "entity": facts[sid][0], "relation": facts[sid][1], "target": facts[sid][2], "revoked": False}
                       for sid in path if sid in sections]
            routes.append({"sources": sources, "queries": [{"entity": entity, "relations": relations}]})
        cases.append({"id": name, "question": question, "expected": expected, "removed": removed,
                      "sections": sections, "document": "\n\n".join(f"[{k}] {v}" for k, v in sections.items()), "routes": routes})
    return {"title": "Atlas and Orion — continuity handbook", "language": "en",
            "annotation": "Human-authored structured facts and routes; no automatic text-to-DNA extraction",
            "document": "\n\n".join(f"[{k}] {v}" for k, v in PARAGRAPHS.items()), "cases": cases}
