use super::memory::Fact;

pub fn evidence_prompt(entity: &str, facts: &[Fact]) -> String {
    let mut prompt = String::from("Use only the evidence. Find the person assigned to the locker containing the parcel. Answer A, B, C, D, or UNKNOWN if either link is missing.\n\nEvidence:\nParcel example is stored in locker unit.\nLocker unit is assigned to B.\nQuestion: Who is assigned to the locker containing parcel example?\nAnswer: B\n\nEvidence:\nParcel lost is stored in locker absent.\nQuestion: Who is assigned to the locker containing parcel lost?\nAnswer: UNKNOWN\n\nEvidence:\n");
    for fact in facts {
        let line = match fact.relation.as_str() {
            "stored_at" => format!(
                "Parcel {} is stored in locker {}.\n",
                fact.entity, fact.target
            ),
            "assigned_to" => format!("Locker {} is assigned to {}.\n", fact.entity, fact.target),
            _ => format!("{} {} {}.\n", fact.entity, fact.relation, fact.target),
        };
        prompt.push_str(&line);
    }
    prompt.push_str(&format!(
        "Question: Who is assigned to the locker containing parcel {entity}?\nAnswer:"
    ));
    prompt
}
