mod survival_support;
use serde_json::json;
use std::{fs, io::Write, path::Path, time::Instant};
use tron_v2::{
    crypto,
    network::{recipe::replay, regeneration::regenerate},
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 1 {
        return Err("Use a new output directory".into());
    }
    let folder = Path::new(&args[0]);
    fs::create_dir(folder)?;
    let mut events = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(folder.join("trials.jsonl"))?;
    let mut passed = 0;
    for seed in 0..20u8 {
        let started = Instant::now();
        let key = crypto::random::<32>();
        let (root, leaf, node, expected) = survival_support::genesis(seed, &key)?;
        let expanded = regenerate(&root, &key, &[node], 100)?;
        let ids: Vec<_> = (0..5).map(|n| (seed as usize * 7 + n * 17) % 100).collect();
        let survivors: Vec<_> = ids.iter().map(|i| expanded.nodes[*i].clone()).collect();
        drop(expanded); // No original network is available to recovery.
        let rebuilt = regenerate(&root, &key, &survivors, 100)?;
        let mut lost = survivors.clone();
        for node in &mut lost {
            node.units.remove(&leaf);
        }
        let missing = regenerate(&root, &key, &lost, 100).is_err();
        let wrong_key = regenerate(&root, &crypto::random::<32>(), &survivors, 100).is_err();
        let mut corrupted = survivors.clone();
        for bytes in corrupted[0].units.values_mut() {
            bytes[0] ^= 1;
        }
        let fallback = regenerate(&root, &key, &corrupted, 100)?.object == expected;
        let mut connected = survivors[..2].to_vec();
        connected[0].units.remove(&leaf);
        connected[1].units.remove(&root);
        let shared = regenerate(&root, &key, &connected, 100)?.object == expected;
        let object_ok = rebuilt.object == expected;
        let proof = replay(&root, &key, |id| {
            rebuilt.nodes[0]
                .units
                .get(id)
                .cloned()
                .into_iter()
                .collect()
        })?;
        let success = object_ok
            && missing
            && wrong_key
            && fallback
            && shared
            && proof.state_hashes.len() == 33;
        passed += usize::from(success);
        let record = json!({"seed":seed,"status":if success {"PASS"} else {"FAIL"},
            "initial_nodes":1,"expanded_nodes":100,"survivor_ids":ids,"surviving_nodes":5,
            "rebuilt_nodes":rebuilt.nodes.len(),"object_exact":object_ok,"verified_steps":proof.state_hashes.len(),
            "missing_content_rejected":missing,"wrong_key_rejected":wrong_key,"corrupt_replica_bypassed":fallback,
            "dependencies_recovered_across_two_incomplete_nodes":shared,"unique_units":rebuilt.unique_units,
            "ciphertext_bytes_across_rebuilt_nodes":rebuilt.stored_bytes,"object_bytes":expected.len(),
            "object_hash":crypto::hash(&rebuilt.object),"seconds":started.elapsed().as_secs_f64()});
        writeln!(events, "{record}")?;
    }
    events.sync_all()?;
    let summary = json!({"trials":20,"passed":passed,"scope":"In-process storage nodes, full replication, no remote services or automatic membership",
        "survival_condition":"Enough complete verified content plus externally retained root and key",
        "key_storage":"Fresh ephemeral key per trial; not included in output; no durable key service"});
    fs::write(
        folder.join("summary.json"),
        serde_json::to_vec_pretty(&summary)?,
    )?;
    println!("{summary}");
    if passed != 20 {
        return Err("Survival characterization failed".into());
    }
    Ok(())
}
