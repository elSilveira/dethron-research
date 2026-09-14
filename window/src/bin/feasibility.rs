use serde_json::json;
use std::{collections::BTreeSet, time::Instant};
use tron_v2::{task::factorize, trit::Trit, tron::Tron};

// Inputs exclude every hard-coded evolution fixture. No results feed selection.
fn workload(seed: u64) -> Vec<u64> {
    let mut state = seed;
    let mut numbers = BTreeSet::new();
    while numbers.len() < 256 {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        numbers.insert(2000 + (state >> 32) % 18000);
    }
    numbers.into_iter().collect()
}

fn reference(mut number: u64) -> Vec<u64> {
    let mut result = Vec::new();
    let upper = number;
    for divisor in 2..=upper {
        while number % divisor == 0 {
            result.push(divisor);
            number /= divisor;
        }
        if number == 1 {
            break;
        }
    }
    result
}

fn measure(numbers: &[u64], strategy: Trit) -> (u64, u128, Vec<Vec<u64>>) {
    let start = Instant::now();
    let work: Vec<_> = numbers
        .iter()
        .map(|n| factorize(*n, strategy, 1_000_000).expect("valid workload"))
        .collect();
    let elapsed = start.elapsed().as_nanos();
    let divisions = work.iter().map(|w| w.divisions).sum();
    (
        divisions,
        elapsed,
        work.into_iter().map(|w| w.factors).collect(),
    )
}

fn main() {
    let mut runs = Vec::new();
    for seed in 1..=10 {
        let numbers = workload(seed);
        let expected: Vec<_> = numbers.iter().map(|n| reference(*n)).collect();
        let start = Instant::now();
        let mut adaptive = Tron::new(0);
        let selection = adaptive.evolve();
        let selection_ns = start.elapsed().as_nanos();
        let strategies = [Trit::Minus, Trit::Zero, Trit::Plus, adaptive.strategy()];
        let mut divisions = [0_u64; 4];
        let mut times = [0_u128; 4];
        // Rotate timing order to reduce systematic first/last-arm bias.
        for offset in 0..4 {
            let arm = (seed as usize + offset) % 4;
            let (cost, elapsed, answers) = measure(&numbers, strategies[arm]);
            assert_eq!(answers, expected, "incorrect factors in arm {arm}");
            divisions[arm] = cost;
            times[arm] = elapsed;
        }
        runs.push(
            json!({"seed":seed, "held_out_count":numbers.len(), "inputs":numbers,
            "fixed_divisions":&divisions[..3], "fixed_ns":&times[..3],
            "adaptive_divisions":divisions[3], "adaptive_kernel_ns":times[3],
            "selection_divisions":selection.evaluation_divisions, "selection_ns":selection_ns,
            "total_adaptive_divisions":divisions[3]+selection.evaluation_divisions,
            "total_adaptive_ns":times[3]+selection_ns,
            "selected_strategy":adaptive.strategy()}),
        );
    }
    println!("{}", serde_json::to_string_pretty(&json!({
        "schema":1, "correct":true, "runs":runs,
        "scope":"v2 fixed candidate selection; no path reorganization or distribution",
        "controls":["Minus", "Zero", "Plus"],
        "cache_enabled":false,
        "timing_scope":"kernel batches; adaptive also includes identity creation and one audited evolution; excludes verification and JSON",
        "limits":"division counts are not energy; timings exploratory; no full runtime memory or per-task audit comparison"
    })).unwrap());
}
