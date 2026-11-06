import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import portable
from deepseek_nonthinking import NonThinkingRunner
class TransportTests(unittest.TestCase):
 def test_deepseek_only(self):
  body={'model':'deepseek-v4-pro','messages':[],'max_tokens':7000}; before=copy.deepcopy(body)
  obj=object.__new__(NonThinkingRunner)
  with patch.object(portable.Runner,'_post_api',return_value={'ok':True}) as post:
   self.assertEqual(obj._post_api('https://api.deepseek.com','/chat/completions',body,'DEEPSEEK_API_KEY'),{'ok':True})
   args=post.call_args.args; self.assertEqual(args[2]['thinking'],{'type':'disabled'}); self.assertEqual(args[2]['model'],'deepseek-v4-pro'); self.assertEqual(body,before)
  with patch.object(portable.Runner,'_post_api',return_value={}) as post:
   obj._post_api('https://api.openai.com/v1','/chat/completions',body,'OPENAI_API_KEY'); self.assertEqual(post.call_args.args[2],body)
if __name__=='__main__': unittest.main()
