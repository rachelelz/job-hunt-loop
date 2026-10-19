"""Offline regressions for malformed feeds/config and private state handling."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('poll', ROOT / 'scripts/poll_boards.py')
poll = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poll)

class PollTests(unittest.TestCase):
    def test_invalid_vendor_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / 'watchlist.json'
            cfg.write_text(json.dumps({'boards': [{'vendor': 'unknown', 'slug': 'test'}]}))
            result = subprocess.run([sys.executable, str(ROOT/'scripts/poll_boards.py'), '--config', str(cfg)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('no valid boards', result.stderr)

    def test_unrepresentable_timestamp_is_undated(self):
        for value in [float('inf'), float('nan'), 10**100, 'bad date']:
            self.assertIsNone(poll.parse_date(value))

    def test_bad_state_shapes_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'seen.json'
            for state in [{'seen': []}, {'zero_runs': []}, {'zero_runs': {'x': {'count': 'three'}}}]:
                path.write_text(json.dumps(state))
                with self.assertRaises(SystemExit):
                    poll.load_state(str(path))

    def test_private_atomic_state_ignores_predictable_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'seen.json'
            victim = Path(tmp)/'unrelated.txt'
            victim.write_text('keep')
            Path(str(path)+'.tmp').symlink_to(victim)
            state = {'seen': {'lever:demo:1':'2026-10-19'}, 'zero_runs': {}}
            poll.save_state(str(path), state)
            self.assertEqual(victim.read_text(), 'keep')
            self.assertEqual(poll.load_state(str(path)), state)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_no_save_does_not_consume_posting(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)/'watchlist.json'; state = Path(tmp)/'seen.json'
            cfg.write_text(json.dumps({'boards':[{'vendor':'lever','slug':'demo'}]}))
            posting = {'id':'1','title':'Analyst','location':'Denver','published':None,'url':'https://example.com/job','extra':''}
            args = ['poll', '--config', str(cfg), '--state', str(state), '--json', '--no-save']
            with patch.object(sys, 'argv', args), patch.dict(poll.VENDORS, {'lever': lambda _: [posting]}), contextlib.redirect_stdout(io.StringIO()) as out:
                poll.main()
            self.assertEqual(json.loads(out.getvalue())['totals']['new'], 1)
            self.assertFalse(state.exists())

    def test_whole_word_and_remote_filter(self):
        self.assertFalse(poll.matches({'title':'Retail analyst','location':'Denver'}, ['ai'], [], []))
        self.assertTrue(poll.matches({'title':'Internal analyst','location':'Denver'}, [], ['intern'], ['denver']))
        self.assertTrue(poll.matches({'title':'Analyst','location':'','remote':True}, [], [], ['remote']))
        self.assertFalse(poll.matches({'title':'Analyst','location':'Remote, US','remote':True}, [], [], ['germany']))

class RenderTests(unittest.TestCase):
    def test_same_path_and_bad_page_limit_preserve_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = Path(tmp)/'input.html'; html.write_text('<p>keep</p>')
            for output, limit in [(html,'2'), (Path(tmp)/'out.pdf','bad')]:
                result = subprocess.run(['bash',str(ROOT/'scripts/render_pdf.sh'),str(html),str(output),limit],capture_output=True)
                self.assertEqual(result.returncode,2)
                self.assertEqual(html.read_text(),'<p>keep</p>')

    def test_browser_failure_preserves_existing_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            html=Path(tmp)/'in.html'; html.write_text('<p>Example</p>')
            pdf=Path(tmp)/'out.pdf'; pdf.write_bytes(b'old pdf')
            env=dict(os.environ,CHROME_BIN='/usr/bin/false')
            result=subprocess.run(['bash',str(ROOT/'scripts/render_pdf.sh'),str(html),str(pdf)],env=env,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(pdf.read_bytes(),b'old pdf')
            self.assertFalse(list(Path(tmp).glob('.job-hunt-render.*')))


class VendorTests(unittest.TestCase):
    def test_vendor_normalization_and_remote_semantics(self):
        fixtures = {
            'greenhouse': {'jobs':[{'id':1,'title':' Analyst ','location':{'name':'Denver'},'absolute_url':'https://example.com/1'}]},
            'lever': [{'id':'2','text':'Analyst','categories':{'allLocations':['Denver','Boulder']},'workplaceType':'hybrid'}],
            'lever-eu': [{'id':'3','text':'Analyst','categories':{},'workplaceType':'remote'}],
            'ashby': {'jobs':[{'id':'4','title':'Analyst','location':'Denver','isRemote':True,'workplaceType':'Hybrid'}]},
            'recruitee': {'offers':[{'id':5,'title':'Analyst','location':'Denver','remote':True,'status':'published'},{'id':6,'status':'draft'}]},
            'workable': {'jobs':[{'shortcode':'7','title':'Analyst','city':'Denver','country':'US','telecommuting':False},{'shortcode':'7','title':'Analyst','city':'Boulder','country':'US','telecommuting':True}]},
        }
        normalized = {}
        for vendor, data in fixtures.items():
            with self.subTest(vendor=vendor), patch.object(poll, 'fetch_json', return_value=data):
                jobs = poll.VENDORS[vendor]('example')
                self.assertEqual(len(jobs),1)
                self.assertEqual(jobs[0]['title'],'Analyst')
                normalized[vendor]=jobs[0]
        self.assertFalse(normalized['lever']['remote'])
        self.assertTrue(normalized['lever-eu']['remote'])
        self.assertFalse(normalized['ashby']['remote'])
        self.assertTrue(normalized['workable']['remote'])
        self.assertIn('Boulder',normalized['workable']['location'])

    def test_slugs_cannot_escape_vendor_url(self):
        for value in ['../private','example/other','example?token=x','example\n','example@localhost','..',None]:
            self.assertFalse(poll.valid_slug(value,'lever'),repr(value))
        self.assertTrue(poll.valid_slug('mistral.ai','ashby'))
        self.assertFalse(poll.valid_slug('mistral.ai','recruitee'))

if __name__ == '__main__':
    unittest.main()
