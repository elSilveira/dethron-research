use std::io::Write;
use std::path::Path;
use tron_v2::network::{
    node_control::{genesis, repair, Authority},
    node_store::Store,
};
fn run() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    match args.as_slice() {
        [op, directory, ready] if op == "serve" => {
            tron_v2::network::node_wire::serve(Path::new(directory), Path::new(ready))
        }
        [op, directory, owner] if op == "genesis" => {
            let mut file = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(owner)
                .map_err(|e| e.to_string())?;
            let text = format!(
                "TRON genesis {}: persistent reconstruction from surviving encrypted inputs.",
                tron_v2::crypto::hash(&tron_v2::crypto::random::<32>())
            );
            let authority = genesis(&Store::open(Path::new(directory))?, text.as_bytes())?;
            file.write_all(&serde_json::to_vec(&authority).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
            file.sync_all().map_err(|e| e.to_string())?;
            println!(
                "{}",
                serde_json::json!({"root":authority.root,"expected_hash":authority.expected_hash,"object_bytes":text.len()})
            );
            Ok(())
        }
        [op, config] if op == "repair" => {
            let value: serde_json::Value =
                serde_json::from_slice(&std::fs::read(config).map_err(|e| e.to_string())?)
                    .map_err(|e| e.to_string())?;
            let owner = value["authority"]
                .as_str()
                .ok_or("Missing authority path")?;
            let authority: Authority =
                serde_json::from_slice(&std::fs::read(owner).map_err(|e| e.to_string())?)
                    .map_err(|e| e.to_string())?;
            let donors: Vec<String> =
                serde_json::from_value(value["donors"].clone()).map_err(|e| e.to_string())?;
            let targets: Vec<String> =
                serde_json::from_value(value["targets"].clone()).map_err(|e| e.to_string())?;
            println!("{}", repair(&authority, &donors, &targets)?);
            Ok(())
        }
        _ => Err("Use: dna_node serve DIRECTORY NEW_READY_FILE".into()),
    }
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
