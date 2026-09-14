mod experiment;
mod lineage;
mod stream;

fn execute() -> Result<(), String> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() != 2 {
        return Err("Usage: tron-window <cycles:1..100> <step-delay-ms:0..2000>".into());
    }
    let cycles = args[0].parse::<usize>().map_err(|_| "Invalid cycles")?;
    let delay = args[1].parse::<u64>().map_err(|_| "Invalid step delay")?;
    if !(1..=100).contains(&cycles) || delay > 2000 {
        return Err("Cycles must be 1..100; step delay must be 0..2000 ms".into());
    }
    experiment::run(cycles, &mut stream::Stream::new(delay))
}

fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
