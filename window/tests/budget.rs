use tron_window::budget::{Activity, Budget, Exhausted};

#[test]
fn all_learning_and_execution_share_one_limit() {
    let mut budget = Budget::new(6);
    for activity in [
        Activity::Execute,
        Activity::Explore,
        Activity::Update,
        Activity::Consolidate,
        Activity::Reconstruct,
        Activity::Validate,
    ] {
        assert_eq!(budget.charge(activity, 1), Ok(()));
        assert_eq!(budget.spent(activity), 1);
    }
    assert_eq!(budget.remaining(), 0);
    assert_eq!(budget.charge(Activity::Execute, 1), Err(Exhausted));
}

#[test]
fn rejected_work_does_not_erase_previous_cost() {
    let mut budget = Budget::new(10);
    budget.charge(Activity::Explore, 7).unwrap();
    assert_eq!(budget.charge(Activity::Consolidate, 4), Err(Exhausted));
    assert_eq!(budget.remaining(), 3);
    assert_eq!(budget.spent(Activity::Explore), 7);
    assert_eq!(budget.spent(Activity::Consolidate), 0);
}

#[test]
fn huge_charge_cannot_overflow_into_free_work() {
    let mut budget = Budget::new(u64::MAX);
    budget.charge(Activity::Execute, 1).unwrap();
    assert_eq!(budget.charge(Activity::Update, u64::MAX), Err(Exhausted));
    assert_eq!(budget.remaining(), u64::MAX - 1);
}
