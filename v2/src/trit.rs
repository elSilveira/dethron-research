use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Trit {
    Minus,
    Zero,
    Plus,
}

// Five base-3 digits fit in a byte (3^5 = 243); CPUs remain binary.
pub fn pack(values: &[Trit]) -> Vec<u8> {
    values
        .chunks(5)
        .map(|chunk| {
            let mut byte = 0;
            let mut place = 1;
            for value in chunk {
                byte += match value {
                    Trit::Minus => 0,
                    Trit::Zero => 1,
                    Trit::Plus => 2,
                } * place;
                if place < 81 {
                    place *= 3;
                }
            }
            byte
        })
        .collect()
}

pub fn unpack(bytes: &[u8], len: usize) -> Result<Vec<Trit>, String> {
    if bytes.len() != len.div_ceil(5) {
        return Err("Invalid packed length".into());
    }
    let mut values = Vec::with_capacity(len);
    for byte in bytes {
        let count = (len - values.len()).min(5);
        if u16::from(*byte) >= 3_u16.pow(count as u32) {
            return Err("Noncanonical trit encoding".into());
        }
        let mut digit = *byte;
        for _ in 0..count {
            values.push([Trit::Minus, Trit::Zero, Trit::Plus][(digit % 3) as usize]);
            digit /= 3;
        }
    }
    Ok(values)
}
