"""Fixed bounded secondary queries; no monitor-thread or heartbeat dependency."""
import threading,os
from bounded_sampler import query
from baseline_contract import save
class SecondarySampler:
 def __init__(self,root,tree,launched,ledger):
  self.root=root;self.tree=tree;self.launched=launched;self.ledger=ledger;self.stop=threading.Event();self.rows=[];self.thread=threading.Thread(target=self.run,name='secondary-sampler');self.thread.start()
 def run(self):
  try:
   while not self.stop.is_set():
    x=query(self.root,'normal',len(self.rows),self.stop,self.tree);self.rows.append(x)
    if x.get('pid'):self.launched.append(dict(pid=x['pid'],created=x['created'],image=x.get('image','UNKNOWN'),role='secondary-sampler',parentPid=os.getpid()))
    if not x.get('allExited') or not x.get('handleClosed'):raise RuntimeError('Required sampler cleanup unproven')
    if self.stop.wait(10):break
  except BaseException:self.ledger.fail('secondary-sampler-cleanup')
 def close(self):
  self.stop.set();self.thread.join(6)
  if self.thread.is_alive():self.ledger.fail('secondary-sampler-close','Supervisor did not exit within bounded close')
  save(self.root/'sampler-results.json',dict(secondary=True,threadExited=not self.thread.is_alive(),queries=self.rows,missing=sum(x['status']!='AVAILABLE' for x in self.rows)))
