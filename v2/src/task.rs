use crate::trit::Trit;

#[derive(Debug, PartialEq, Eq)]
pub struct Work {
    pub factors: Vec<u64>,
    pub divisions: u64,
}

pub fn factorize(n: u64, strategy: Trit, budget: u64) -> Result<Work, String> {
    if !(1..=1_000_000).contains(&n) || !(1..=1_000_000).contains(&budget) {
        return Err("Input/budget outside [1, 1000000]".into());
    }
    let (mut remaining, mut divisor, mut divisions) = (n, 2, 0);
    let mut factors = Vec::new();
    while remaining > 1 {
        if strategy != Trit::Minus && divisor * divisor > remaining {
            factors.push(remaining);
            break;
        }
        if divisions == budget {
            return Err("Division budget exhausted".into());
        }
        divisions += 1;
        if remaining % divisor == 0 {
            factors.push(divisor);
            remaining /= divisor;
        } else {
            divisor += if strategy == Trit::Plus && divisor > 2 {
                2
            } else {
                1
            };
        }
    }
    Ok(Work { factors, divisions })
}
