use crate::{
    task::factorize,
    trit::Trit,
    tron::{Evolution, Tron},
};
use serde_json::json;

const TRAIN: &[(u64, &[u64])] = &[(97, &[97]), (121, &[11, 11]), (221, &[13, 17])];
const VALIDATE: &[(u64, &[u64])] = &[
    (997, &[997]),
    (49, &[7, 7]),
    (84, &[2, 2, 3, 7]),
    (1, &[]),
    (2, &[2]),
];

fn score(strategy: Trit, cases: &[(u64, &[u64])]) -> Result<u64, String> {
    let mut cost = 0;
    for (number, expected) in cases {
        let work = factorize(*number, strategy, 2000)?;
        if work.factors != *expected {
            return Err("Candidate produced wrong answer".into());
        }
        cost += work.divisions;
    }
    Ok(cost)
}

impl Tron {
    // Candidate code is reviewed and fixed; evolution selects a bounded gene.
    pub fn evolve(&mut self) -> Evolution {
        let mut report = Evolution {
            promoted: false,
            evaluation_divisions: 0,
            before_divisions: 0,
            after_divisions: 0,
        };
        if self.ready().is_err() {
            return report;
        }
        let old = self.state.strategy;
        let mut best = old;
        let mut best_cost = score(old, TRAIN).expect("Valid reference strategy");
        report.evaluation_divisions += best_cost;
        for candidate in [Trit::Minus, Trit::Zero, Trit::Plus] {
            if let Ok(cost) = score(candidate, TRAIN) {
                report.evaluation_divisions += cost;
                if cost < best_cost {
                    best = candidate;
                    best_cost = cost;
                }
            }
        }
        let before = score(old, VALIDATE).expect("Valid reference strategy");
        let after = score(best, VALIDATE).expect("Validated candidate strategy");
        report.evaluation_divisions += before + after;
        report.before_divisions = before;
        report.after_divisions = after;
        if after < before {
            self.state.strategy = best;
            self.state.version += 1;
            report.promoted = true;
        }
        self.audit.append(
            "evolution",
            json!({"from":old,"to":self.state.strategy,
            "version":self.state.version,"measurement":report}),
            None,
        );
        report
    }
}
