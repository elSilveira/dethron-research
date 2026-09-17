//! Disk-backed demonstration; key stays outside encrypted unit directories.
use std::{fs, io::Write, path::Path};
use tron_v2::{
    crypto,
    network::recovery_plan::{preserve_plan, recover_plan},
};

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn std::error::Error>> {
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 4 {
        return Err("Use: preserve|recover input-or-root directory key-file".into());
    }
    let directory = Path::new(&args[2]);
    let key_path = Path::new(&args[3]);
    match args[0].as_str() {
        "preserve" => {
            let plan = serde_json::from_slice(&fs::read(&args[1])?)?;
            let key = crypto::random::<32>();
            let (root, store) = preserve_plan(&plan, &key)?;
            fs::create_dir(directory)?;
            fs::create_dir(directory.join("primary"))?;
            fs::create_dir(directory.join("replica"))?;
            write_new(key_path, &key)?;
            for (id, bytes) in &store {
                write_new(&directory.join("primary").join(id), bytes)?;
                write_new(&directory.join("replica").join(id), bytes)?;
            }
            write_new(&directory.join("trusted-root.txt"), root.as_bytes())?;
            println!(
                "{}",
                serde_json::json!({"root":root,"units":store.len(),"replicas":2})
            );
        }
        "recover" => {
            let key: [u8; 32] = fs::read(key_path)?
                .try_into()
                .map_err(|_| "Invalid key length")?;
            let mut fetched = 0;
            let plan = recover_plan(&args[1], &key, |id| {
                fetched += 1;
                ["primary", "replica"]
                    .iter()
                    .filter_map(|folder| fs::read(directory.join(folder).join(id)).ok())
                    .collect()
            })?;
            write_new(
                &directory.join("recovered-config.json"),
                &serde_json::to_vec_pretty(&plan)?,
            )?;
            println!(
                "{}",
                serde_json::json!({"recovered_units":fetched,"tasks":plan["tasks"].as_array().map(Vec::len)})
            );
        }
        _ => return Err("Unknown mode".into()),
    }
    Ok(())
}
