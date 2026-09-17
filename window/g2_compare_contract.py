"""Predeclared paired functional comparison, not a power or throughput benchmark."""
PROFILE = {'version': 1, 'payload_bytes': 49152, 'repeats': 2, 'deadline_seconds': 120,
           'tx_budget_bytes': 2_000_000, 'file_budget_bytes': 8_000_000,
           'limits_kb': {'all': 256, 'loss': 64}, 'policies': ['whole', 'split', 'xor2']}


def cases():
    rows = []
    for repeat in range(PROFILE['repeats']):
        modes = PROFILE['policies'][::1 if repeat == 0 else -1]
        for scenario in ('all', 'loss'):
            contacts = ('CAB' if repeat == 0 else 'BAC') if scenario == 'all' else ('CA' if repeat == 0 else 'BC')
            for mode in modes:
                rows.append({'repeat': repeat, 'scenario': scenario, 'mode': mode, 'contacts': list(contacts),
                             'limit_kb': PROFILE['limits_kb'][scenario]})
    return rows


def expected_completion(mode, scenario, count):
    if mode == 'whole':
        return scenario == 'all' and count >= 1
    return count >= (2 if mode == 'xor2' else 3)


def eligible(tx, files):
    return tx <= PROFILE['tx_budget_bytes'] and files <= PROFILE['file_budget_bytes']
