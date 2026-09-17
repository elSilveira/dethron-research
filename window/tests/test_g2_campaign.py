import unittest

from g2_compare_contract import PROFILE, cases, eligible, expected_completion


class CampaignTests(unittest.TestCase):
    def test_paired_cases_reverse_policy_order_and_rotate_loss(self):
        rows = cases()
        self.assertEqual(len(rows), 12)
        for repeat in range(2):
            for scenario in ('all', 'loss'):
                group = [r for r in rows if r['repeat'] == repeat and r['scenario'] == scenario]
                self.assertEqual({r['mode'] for r in group}, {'whole', 'split', 'xor2'})
                self.assertEqual(len({tuple(r['contacts']) for r in group}), 1)
        self.assertEqual([r['mode'] for r in rows[:3]], list(reversed([r['mode'] for r in rows[6:9]])))
        self.assertNotEqual(rows[3]['contacts'], rows[9]['contacts'])

    def test_budget_failure_is_not_a_success(self):
        self.assertTrue(eligible(1, 1))
        self.assertFalse(eligible(PROFILE['tx_budget_bytes']+1, 1))
        self.assertFalse(eligible(1, PROFILE['file_budget_bytes']+1))

    def test_loss_and_transfer_cap_have_distinct_expectations(self):
        self.assertTrue(expected_completion('whole', 'all', 1))
        self.assertFalse(expected_completion('whole', 'loss', 2))
        self.assertFalse(expected_completion('split', 'loss', 2))
        self.assertTrue(expected_completion('xor2', 'loss', 2))


if __name__ == '__main__':
    unittest.main()
