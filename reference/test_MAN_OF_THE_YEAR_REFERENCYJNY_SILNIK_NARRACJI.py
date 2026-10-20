"""Unittest: behavioral truth table, idempotency, schema, convergence."""
import itertools
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
p=Path(__file__).with_name('MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py')
from importlib.util import spec_from_loader, module_from_spec
import sys
loader=SourceFileLoader('moty_logic',str(p))
spec=spec_from_loader(loader.name,loader)
m=module_from_spec(spec)
sys.modules[spec.name]=m
loader.exec_module(m)

class NarrativeTests(unittest.TestCase):
    def test_all_sixteen_january_paths_enter_canonical_ch59(self):
        for inputs in itertools.product(('PASS','APPROACH'),repeat=4):
            s=m.NarrativeState()
            for n,ch in enumerate(inputs,1):s.record_paulina_opportunity(n,ch)
            result=s.enter_chapter59()
            self.assertTrue(s.paulina_at_icecream_shop)
            self.assertTrue(s.ch59_canonical_event_played)
            self.assertEqual(s.paulina_quests_unlocked, 'APPROACH' in inputs)
            self.assertEqual(result, 'KNOWN_CUSTOMER' if 'APPROACH' in inputs else 'FIRST_MEETING_CUSTOMER')
            self.assertEqual(s.first_meeting_wiola_present, inputs[0]=='APPROACH')
            self.assertEqual(m.NarrativeState.decode(s.encode()),s)

    def test_do_not_overwrite_choice(self):
        s=m.NarrativeState()
        s.record_paulina_opportunity(1,'PASS')
        s.record_paulina_opportunity(1,'PASS')
        self.assertEqual(s.missed_opportunities,1)
        with self.assertRaises(m.TransitionError):s.record_paulina_opportunity(1,'APPROACH')

    def test_reject_out_of_order(self):
        with self.assertRaises(m.TransitionError):m.NarrativeState().record_paulina_opportunity(3,'PASS')

    def test_no_ch59_without_january(self):
        with self.assertRaises(m.TransitionError):m.NarrativeState().enter_chapter59()

    def test_dlc_unlock_once_each_and_stop_after_three(self):
        s=m.NarrativeState()
        for n in range(1,5):s.record_paulina_opportunity(n,'PASS')
        s.enter_chapter59()
        s.completed_chapters=list(range(1,71))
        for n in range(1,5):
            self.assertTrue(s.complete_main_campaign('run-'+str(n)))
            self.assertFalse(s.complete_main_campaign('run-'+str(n)))
        self.assertEqual(s.campaign_completion_count,4)
        self.assertEqual(s.unlocks,['DLC-01','DLC-02','DLC-03'])

    def test_completion_requires_all_70(self):
        s=m.NarrativeState()
        for n in range(1,5):s.record_paulina_opportunity(n,'PASS')
        s.enter_chapter59()
        s.completed_chapters=list(range(1,70))
        with self.assertRaises(m.TransitionError):s.complete_main_campaign('run-1')

    def test_reject_mutated_schema(self):
        s=m.NarrativeState().encode()
        j=json.loads(s);j['unknown']='x'
        with self.assertRaises(m.TransitionError):m.NarrativeState.decode(json.dumps(j))

    def test_immutability_v1_guards(self):
        s=m.NarrativeState()
        s.paulina_at_icecream_shop=False
        s.ch59_canonical_event_played=True
        with self.assertRaises(m.TransitionError):s.validate()

if __name__=='__main__':unittest.main(verbosity=2)
