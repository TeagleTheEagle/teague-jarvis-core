"""Exact diagnostic sidecar admission; never interprets samples as lifecycle proof."""
import pathlib
from workspace_binding_v4 import read,sha,need,safe
SIDECARS={'loss-diagnostic-v2.json':('authority','etw-ready.json','etw-result.json'),'detail/loss-diagnostic-v2.json':('detail','detail/etw-ready.json','detail/etw-result.json')}
def inspect(root,strict=True):
 root=pathlib.Path(root);rows=[];errors=[]
 for name,(channel,ready,result) in SIDECARS.items():
  try:
   p=safe(root/name,root);need(p.is_file(),'MISSING_SIDECAR');before=sha(p);v=read(p)
   need(v.get('schema')=='stage6-loss-diagnostic-v2','SIDECAR_SCHEMA');need(v.get('run')==root.name,'SIDECAR_RUN')
   r=read(safe(root/ready,root));need(v.get('session')==r['session'] and v.get('channel')==channel,'SIDECAR_SESSION')
   need(v.get('frequency')==r['frequency'] and v.get('diagnosticOnly') is True and v.get('acceptanceSealed') is False,'SIDECAR_AUTHORITY')
   if (root/result).exists():need(read(root/result)['session']==v['session'],'SIDECAR_FINAL_SESSION')
   need(sha(p)==before,'SIDECAR_CHANGED');rows.append(dict(path=name,sha256=before,bytes=p.stat().st_size,diagnosticOnly=True,acceptanceAuthority=False))
  except (OSError,ValueError,KeyError,TypeError) as e:errors.append(dict(path=name,error=str(e)))
 if strict:need(not errors,'DIAGNOSTIC_FORMAT:'+str(errors))
 return dict(schema='stage6-diagnostic-admission-v4',files=rows,errors=errors,complete=not errors,acceptanceAuthority=False)
