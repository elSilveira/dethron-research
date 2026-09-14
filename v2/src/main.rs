use std::{fs::OpenOptions, io::Write};

fn execute(args: &[String]) -> Result<(), String> {
    if args.is_empty() || args == ["--help"] {
        println!(
            "tron-v2 probe [cycles:1..100] [new-report.json]\n\
                  Runs bounded evolution, inheritance, privacy and ternary encoding probes.\n\
                  Emits public evidence only. No quantum hardware or background daemon."
        );
        return Ok(());
    }
    if args[0] != "probe" || args.len() > 3 {
        return Err("Use --help for usage".into());
    }
    let cycles = args
        .get(1)
        .map(|s| s.parse::<usize>())
        .transpose()
        .map_err(|_| "Invalid cycle count")?
        .unwrap_or(3);
    let report = tron_v2::probe::run(cycles)?;
    let bytes = serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?;
    if let Some(path) = args.get(2) {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| format!("Cannot create new report: {e}"))?;
        file.write_all(&bytes).map_err(|e| e.to_string())?;
        file.sync_all().map_err(|e| e.to_string())?;
        println!("Public report saved: {path}");
    } else {
        std::io::stdout()
            .write_all(&bytes)
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = execute(&std::env::args().skip(1).collect::<Vec<_>>()) {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
