use tron_v2::{
    task::factorize,
    trit::{pack, unpack, Trit::*},
};

#[test]
fn ternary_packing_roundtrips_and_rejects_noncanonical_inputs() {
    for len in 0..32 {
        let values: Vec<_> = (0..len).map(|i| [Minus, Zero, Plus][i % 3]).collect();
        let bytes = pack(&values);
        assert_eq!(bytes.len(), len.div_ceil(5));
        assert_eq!(unpack(&bytes, len).unwrap(), values);
    }
    assert!(unpack(&[255], 5).is_err());
    assert!(unpack(&[3], 1).is_err());
    assert!(unpack(&[0, 0], 1).is_err());
}

#[test]
fn all_strategies_compute_correct_factors() {
    for strategy in [Minus, Zero, Plus] {
        for (n, expected) in [
            (1, vec![]),
            (49, vec![7, 7]),
            (84, vec![2, 2, 3, 7]),
            (997, vec![997]),
        ] {
            assert_eq!(factorize(n, strategy, 2000).unwrap().factors, expected);
        }
    }
}

#[test]
fn real_cost_decreases_and_work_is_bounded() {
    let slow = factorize(997, Minus, 2000).unwrap();
    let fast = factorize(997, Plus, 2000).unwrap();
    assert!(fast.divisions < slow.divisions / 10);
    assert!(factorize(997, Minus, 3).is_err());
    assert!(factorize(0, Minus, 100).is_err());
    assert!(factorize(1_000_001, Plus, 100).is_err());
}

#[test]
fn every_three_state_block_and_all_small_factorizations_are_valid() {
    for byte in 0..243 {
        let values = unpack(&[byte], 5).unwrap();
        assert_eq!(pack(&values), vec![byte]);
    }
    // Independent sieve oracle, rather than comparing two implementations of division.
    let mut prime = vec![true; 5001];
    prime[0] = false;
    prime[1] = false;
    for p in 2..=5000 {
        if prime[p] {
            for multiple in (p * 2..=5000).step_by(p) {
                prime[multiple] = false;
            }
        }
    }
    for n in 1..=5000 {
        for strategy in [Minus, Zero, Plus] {
            let result = factorize(n, strategy, 6000).unwrap();
            assert_eq!(result.factors.iter().product::<u64>(), n);
            assert!(result.factors.iter().all(|p| prime[*p as usize]));
            assert!(result.factors.windows(2).all(|pair| pair[0] <= pair[1]));
        }
    }
}
