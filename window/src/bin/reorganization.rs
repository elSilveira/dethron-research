use tron_window::reorganization::probe::{benchmark, demonstrate};

fn execute() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let report = match args.as_slice() {
        [command] if command == "demo" => demonstrate()?,
        [command, seeds] if command == "bench" => {
            benchmark(seeds.parse().map_err(|_| "Invalid seeds")?)?
        }
        _ => return Err("Usage: reorganization demo | bench <seeds:1..100>".into()),
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    Ok(())
}

fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
