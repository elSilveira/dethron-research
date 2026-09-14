use crate::trit::{pack, unpack, Trit};
use serde_json::{json, Value};
use std::{hint::black_box, time::Instant};

fn pack_two(values: &[Trit]) -> Vec<u8> {
    values
        .chunks(4)
        .map(|chunk| {
            chunk.iter().enumerate().fold(0, |byte, (i, trit)| {
                let code = match trit {
                    Trit::Minus => 0,
                    Trit::Zero => 1,
                    Trit::Plus => 2,
                };
                byte | (code << (2 * i))
            })
        })
        .collect()
}

fn unpack_two(bytes: &[u8], len: usize) -> Vec<Trit> {
    (0..len)
        .map(|i| {
            [Trit::Minus, Trit::Zero, Trit::Plus][((bytes[i / 4] >> (2 * (i % 4))) & 3) as usize]
        })
        .collect()
}

pub fn run() -> Value {
    let len = 100_000;
    let repeats = 10;
    let values: Vec<_> = (0..len)
        .map(|i| [Trit::Minus, Trit::Zero, Trit::Plus][i % 3])
        .collect();
    let packed = pack(&values);
    let two = pack_two(&values);
    let mut trit_encode = 0;
    let mut binary_encode = 0;
    let mut trit_decode = 0;
    let mut binary_decode = 0;
    // Warm both paths; alternate their order to reduce fixed-order bias.
    black_box(unpack(&packed, len).unwrap());
    black_box(unpack_two(&two, len));
    for iteration in 0..repeats {
        for ternary in if iteration % 2 == 0 {
            [true, false]
        } else {
            [false, true]
        } {
            let start = Instant::now();
            if ternary {
                black_box(pack(black_box(&values)));
            } else {
                black_box(pack_two(black_box(&values)));
            }
            let encode = start.elapsed().as_nanos();
            let start = Instant::now();
            if ternary {
                black_box(unpack(black_box(&packed), len).unwrap());
            } else {
                black_box(unpack_two(black_box(&two), len));
            }
            let decode = start.elapsed().as_nanos();
            if ternary {
                trit_encode += encode;
                trit_decode += decode;
            } else {
                binary_encode += encode;
                binary_decode += decode;
            }
        }
    }
    json!({"symbols":len,"repeats":repeats,"trit_bytes":packed.len(),
        "two_bit_bytes":two.len(),"byte_per_symbol_bytes":len,
        "trit_encode_ns":trit_encode,"two_bit_encode_ns":binary_encode,
        "trit_decode_ns":trit_decode,"two_bit_decode_ns":binary_decode,
        "roundtrip":unpack(&packed,len).unwrap()==values && unpack_two(&two,len)==values,
        "scope":"payload only; length/header excluded; totals across repeats",
        "decision":"packing saves space; latency tradeoff must be measured per workload"})
}
