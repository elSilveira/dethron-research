use super::{
    dna::{Dna, Query, Source},
    Task,
};

pub struct Case {
    pub task: Task,
    pub expected: String,
    pub kind: String,
    pub corpus: Dna,
}
const EXAMPLES: &str = "Use only CURRENT evidence. If a link is missing or conflicting, answer UNKNOWN.\n\nEvidence:\nParcel example is stored in locker unit.\nLocker unit is assigned to B.\nQuestion: Who is assigned to the locker containing parcel example?\nAnswer: B\n\nEvidence:\nParcel lost is stored in locker absent.\nQuestion: Who is assigned to the locker containing parcel lost?\nAnswer: UNKNOWN\n\nEvidence:\nParcel clash is stored in locker shared.\nLocker shared is assigned to A.\nLocker shared is assigned to C.\nQuestion: Who is assigned to the locker containing parcel clash?\nAnswer: UNKNOWN\n\n";

pub fn cases(split: &str, policy: &str) -> Result<Vec<Case>, String> {
    if !["raw", "examples", "recognized"].contains(&policy) {
        return Err("Unknown accuracy policy".into());
    }
    let (count, supported) = match split {
        "calibration" => (8, 4),
        "heldout" => (40, 20),
        "expansion" => (8, 8),
        _ => return Err("Unknown dataset split".into()),
    };
    let mut cases = Vec::new();
    for index in 0..count {
        let kind = if index < supported {
            "supported"
        } else {
            ["missing", "conflict", "stale", "revoked", "foreign"][(index - supported) % 5]
        };
        let context = format!("{split}-{index}");
        let parcel = format!("{split}_p{index}");
        let locker = format!("{split}_l{index}");
        let owner = ["A", "B", "C", "D"][(index * 3 + 1) % 4];
        let source = |id: &str, entity: &str, relation: &str, target: &str| Source {
            id: format!("{context}-{id}"),
            context: context.clone(),
            revision: 2,
            entity: entity.into(),
            relation: relation.into(),
            target: target.into(),
            revoked: false,
        };
        let mut sources = vec![source("location", &parcel, "stored_at", &locker)];
        let mut ownership = source("owner", &locker, "assigned_to", owner);
        match kind {
            "stale" => ownership.revision = 1,
            "revoked" => ownership.revoked = true,
            "foreign" => ownership.context = "other-session".into(),
            _ => {}
        }
        if kind != "missing" {
            sources.push(ownership);
        }
        if kind == "conflict" {
            sources.push(source(
                "contradiction",
                &locker,
                "assigned_to",
                if owner == "A" { "D" } else { "A" },
            ));
        }
        for noise in 0..if split == "expansion" { 128 } else { 3 } {
            sources.push(source(
                &format!("noise-{noise}"),
                &format!("irrelevant_locker_{noise}"),
                "assigned_to",
                "D",
            ));
        }
        let corpus = Dna {
            sources,
            queries: vec![Query {
                entity: parcel.clone(),
                relations: vec!["stored_at".into(), "assigned_to".into()],
            }],
        };
        let mut dna = corpus.clone();
        if policy == "recognized" {
            dna.sources = corpus.recognize(&context, 2);
        }
        let prefix = if policy == "raw" {
            "Use only CURRENT evidence. Answer A, B, C, D, or UNKNOWN if evidence is missing or conflicting.\n\n"
        } else {
            EXAMPLES
        };
        let prompt = format!("{prefix}Evidence:\n{{{{evidence}}}}\nQuestion: Who is assigned to the locker containing parcel {parcel}?\nAnswer:");
        cases.push(Case {
            task: Task {
                id: format!("case-{index}"),
                context,
                revision: 2,
                parents: vec![],
                prompt,
                candidates: [" A", " B", " C", " D", " UNKNOWN"]
                    .map(str::to_string)
                    .to_vec(),
                max_new_tokens: 32,
                dna: Some(dna),
            },
            expected: if kind == "supported" {
                owner.into()
            } else {
                "UNKNOWN".into()
            },
            kind: kind.into(),
            corpus,
        });
    }
    Ok(cases)
}
