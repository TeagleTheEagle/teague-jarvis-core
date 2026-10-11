import pathlib,json
r=pathlib.Path(__file__).parent; rows=[]
for i in range(30):
 p=r/'sharing-probe'/('append-'+str(i)+'.jsonl')
 with p.open('x') as f:f.write(json.dumps({'sequence':1})+'\n')
 with p.open('r') as reader:
  with p.open('a') as writer:writer.write(json.dumps({'sequence':2})+'\n');writer.flush()
  rows.append({'trial':i,'success':[json.loads(s)['sequence'] for s in reader.read().splitlines()]==[1,2]})
(r/'append-control.json').write_text(json.dumps(rows,indent=2))
print('append control',sum(x['success'] for x in rows),'/30')
