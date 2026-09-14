//! Bounded integer specialists and reconstructible procedures, never answer caches.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Primitive {
    Add(i64),
    Multiply(i64),
    Absolute,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Step {
    Primitive(Primitive),
    Affine { scale: i64, bias: i64 },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Recipe {
    steps: Vec<Step>,
}

#[derive(Clone, Debug)]
pub struct Graph {
    pub ids: Vec<u64>,
    pub recipe: Recipe,
}

impl Recipe {
    pub fn new(steps: &[Primitive]) -> Result<Self, String> {
        if steps.is_empty()
            || steps.len() > 8
            || steps.iter().any(|step| match step {
                Primitive::Add(n) | Primitive::Multiply(n) => !(-16..=16).contains(n),
                Primitive::Absolute => false,
            })
        {
            return Err("Use 1..8 primitives with constants in -16..16".into());
        }
        Ok(Self {
            steps: steps.iter().copied().map(Step::Primitive).collect(),
        })
    }
    pub fn steps(&self) -> &[Step] {
        &self.steps
    }
    pub(super) fn inject_fault(&mut self) {
        self.steps[0] = Step::Primitive(Primitive::Add(16));
    }
    pub fn compose(&self) -> Option<Self> {
        for start in 0..self.steps.len().saturating_sub(2) {
            let mut scale = 1_i64;
            let mut bias = 0_i64;
            let mut valid = true;
            for step in &self.steps[start..start + 3] {
                let affine = match step {
                    Step::Primitive(Primitive::Add(n)) => Some((1, *n)),
                    Step::Primitive(Primitive::Multiply(n)) => Some((*n, 0)),
                    Step::Affine { scale, bias } => Some((*scale, *bias)),
                    _ => None,
                };
                if let Some((a, b)) = affine {
                    scale = a.checked_mul(scale)?;
                    bias = a.checked_mul(bias)?.checked_add(b)?;
                } else {
                    valid = false;
                    break;
                }
            }
            if valid {
                let mut steps = self.steps[..start].to_vec();
                steps.push(Step::Affine { scale, bias });
                steps.extend_from_slice(&self.steps[start + 3..]);
                return Some(Self { steps });
            }
        }
        None
    }
    pub fn execute(&self, input: i64) -> Result<i64, String> {
        if !(-1_000_000..=1_000_000).contains(&input) {
            return Err("Input outside -1000000..1000000".into());
        }
        let mut value = input;
        for step in &self.steps {
            value = match step {
                Step::Primitive(Primitive::Add(n)) => value.checked_add(*n),
                Step::Primitive(Primitive::Multiply(n)) => value.checked_mul(*n),
                Step::Primitive(Primitive::Absolute) => value.checked_abs(),
                Step::Affine { scale, bias } => {
                    value.checked_mul(*scale).and_then(|v| v.checked_add(*bias))
                }
            }
            .ok_or("Arithmetic overflow")?;
        }
        Ok(value)
    }
    /// One dispatch plus primitive arithmetic; affine performs multiply and add.
    pub fn work(&self) -> u64 {
        self.steps
            .iter()
            .map(|s| {
                if matches!(s, Step::Affine { .. }) {
                    3
                } else {
                    2
                }
            })
            .sum()
    }
}

impl Graph {
    pub fn rebuild(recipe: Recipe, next_id: &mut u64) -> Self {
        let ids = (0..recipe.steps.len())
            .map(|_| {
                let id = *next_id;
                *next_id += 1;
                id
            })
            .collect();
        Self { ids, recipe }
    }
}
