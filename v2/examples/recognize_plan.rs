//! Explicit evidence selection using v2's existing tested recognizer.
use std::{fs, io::Write};
use tron_v2::network::dna::Dna;
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 2 {
        return Err("Use input.json new-output.json".into());
    }
    let mut plan: serde_json::Value = serde_json::from_slice(&fs::read(&args[0])?)?;
    for task in plan["tasks"].as_array_mut().ok_or("Missing tasks")? {
        let mut dna = Dna::parse(&task["dna"])?;
        dna.sources = dna.recognize(
            task["context"].as_str().ok_or("Missing context")?,
            task["revision"].as_u64().ok_or("Missing revision")?,
        );
        task["dna"] = dna.value();
    }
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&args[1])?;
    file.write_all(&serde_json::to_vec_pretty(&plan)?)?;
    file.sync_all()?;
    Ok(())
}
