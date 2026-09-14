use super::Task;

pub fn expected(round: usize, case: usize) -> String {
    format!(
        "{}, {}",
        ["A", "B"][(case + round) % 2],
        ["A", "B"][(case / 2 + round) % 2]
    )
}
pub fn questions(round: usize, cases: usize, waves: bool) -> Vec<Task> {
    let mut tasks = Vec::new();
    for case in 0..cases {
        let pair = expected(round, case);
        let owners: Vec<_> = pair.split(", ").collect();
        let context = format!("round-{round}-case-{case}");
        let left = format!(
            "Parcel p{case} is stored in locker x{case}. Locker x{case} is assigned to {}.",
            owners[0]
        );
        let right = format!(
            "Parcel q{case} is stored in locker y{case}. Locker y{case} is assigned to {}.",
            owners[1]
        );
        let single = |evidence: &str, parcel: &str| {
            format!(
            "Use only the evidence. Answer A or B.\nEvidence: {evidence}\nQuestion: Who is assigned to the locker containing parcel {parcel}?\nAnswer:")
        };
        let base = Task {
            id: format!("final-{case}"),
            context,
            revision: 1,
            parents: Vec::new(),
            prompt: String::new(),
            candidates: [" A, A", " A, B", " B, A", " B, B"]
                .map(str::to_string)
                .to_vec(),
            max_new_tokens: 32,
            dna: None,
        };
        let mut final_task = base.clone();
        if waves {
            for (label, evidence, parcel) in [
                ("left", &left, format!("p{case}")),
                ("right", &right, format!("q{case}")),
            ] {
                let mut branch = base.clone();
                branch.id = format!("{label}-{case}");
                branch.prompt = single(evidence, &parcel);
                branch.candidates = vec![" A".into(), " B".into()];
                final_task.parents.push(branch.id.clone());
                tasks.push(branch);
            }
            final_task.prompt = format!("Read the intermediate results. Return the output of left-{case}, then the output of right-{case}, separated by a comma. Answer only A, A or A, B or B, A or B, B.\nAnswer:");
        } else {
            final_task.prompt = format!("Use only the evidence.\nEvidence: {left}\n{right}\nQuestion: Who is assigned to the locker containing parcel p{case}, then parcel q{case}? Return the two owners separated by a comma. Answer only A, A or A, B or B, A or B, B.\nAnswer:");
        }
        tasks.push(final_task);
    }
    tasks
}

pub fn generation() -> Vec<Task> {
    let base = Task {id:"proposal".into(),context:"generation-demo".into(),revision:1,parents:vec![],
        prompt:"A local library has two rooms and two reading groups at 10am. Give one short scheduling proposal.\nProposal:".into(),
        candidates:vec![],max_new_tokens:48,dna:None};
    let mut check = base.clone();
    check.id = "constraints".into();
    check.prompt = "A local library has two rooms and two reading groups at 10am. List two constraints a schedule must satisfy.\nConstraints:".into();
    let mut combine = base.clone();
    combine.id = "synthesis".into();
    combine.parents = vec![base.id.clone(), check.id.clone()];
    combine.max_new_tokens = 64;
    combine.prompt = "Using the proposal and constraints above, write a short final schedule for the two groups.\nSchedule:".into();
    vec![base, check, combine]
}
