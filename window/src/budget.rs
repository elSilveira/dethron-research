//! Shared experimental work budget. Units are explicit work charges, not joules.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Activity {
    Execute,
    Explore,
    Update,
    Consolidate,
    Reconstruct,
    Validate,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Exhausted;

pub struct Budget {
    limit: u64,
    spent: [u64; 6],
}

impl Budget {
    pub fn new(limit: u64) -> Self {
        Self {
            limit,
            spent: [0; 6],
        }
    }

    /// Reserve work before executing it. Failed outcomes do not refund spent work.
    /// A rejected reservation performs no work and leaves previous charges intact.
    pub fn charge(&mut self, activity: Activity, units: u64) -> Result<(), Exhausted> {
        if units > self.remaining() {
            return Err(Exhausted);
        }
        self.spent[activity as usize] += units;
        Ok(())
    }

    pub fn spent(&self, activity: Activity) -> u64 {
        self.spent[activity as usize]
    }

    pub fn remaining(&self) -> u64 {
        self.limit - self.spent.iter().sum::<u64>()
    }
}
