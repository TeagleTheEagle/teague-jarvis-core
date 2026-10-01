def dataset_records(rows, candidate):
 """Compare Windows-relative names without rewriting authoritative records."""
 expected={
  '00.bin':'de2f256064a0af797747c2b97505dc0b9f3df0de4f489eac731c23ae9ca9cc31',
  '01.bin':'916b144867c340614f515c7b0e5415c74832d899c05264ded2a277a6e81d81ff',
  '02.bin':'da1acff5c9defdd68bfa1435c4b43e8d43ed10fcc7cbcb77a85c4482d5f5bda3',
  '03.bin':'3af3f1d870212fe8fcfe6eb321fd14d009bccc953fce3f59f698f0c446a1a39a',
  '04.bin':'ac32e587c08925897c80a703080b055606911082361fbb25198873cfca8b72d0',
  '05.bin':'ac5f57d984b20f78b36a294e26cc99512a1196eb96e4c30d7cec153813e93e1b',
  '06.bin':'570c8bbac0dfe325a89e8193cdb88560d4ce244ac2de3b5226791203107d74f5',
  '07.bin':'07dcb6d11a03624831513672ffdb84d6b1730f54e90aaace444fe3a8ea9b2163',
  '08.bin':'0e7424be9627f88499110c34e21214ed91e026e1657d9be3bd54e3e7e09fd867',
  '09.bin':'83c57546e5a31f700e7adc9edc55118bf2677bd04f0fc9089c6477b1646ffa1f',
  '10.bin':'fbd7cceab2e0f5696b4628188d3d6e4ec3f4222c02638db114d8611cb3b7f2c3',
  '11.bin':'1dfa33e4c49e3c0a9ef0b609c3fb26c5211f7cff763fa72194d884d15d86e68e'}
 candidate=b.safe(pathlib.Path(candidate),pathlib.Path(candidate))
 selected=[];seen=set()
 for row in rows:
  name=row.get('name');b.need(isinstance(name,str) and bool(name),'MALFORMED_MANIFEST_PATH')
  parts=name.replace('/','\\').split('\\')
  win=pathlib.PureWindowsPath(name)
  b.need(not win.drive and not win.root,'ABSOLUTE_MANIFEST_PATH')
  b.need(all(p and p not in ('.','..') and p==p.rstrip(' .') and not any(ord(c)<32 or c in '<>:"|?*' for c in p) for p in parts),'MALFORMED_MANIFEST_PATH')
  key='\\'.join(parts).casefold()
  b.need(key not in seen,'DUPLICATE_NORMALIZED_PATH');seen.add(key)
  if parts[0].casefold()!='small-synthetic':continue
  b.need(len(parts)==2 and parts[0]=='small-synthetic' and parts[1] in expected,'UNEXPECTED_DATASET_ENTRY')
  b.need(type(row.get('bytes')) is int and row['bytes']==65536,'DATASET_SIZE')
  b.need(row.get('sha256')==expected[parts[1]],'DATASET_EXPECTED_HASH')
  selected.append((row,parts))
 b.need(len(selected)==12 and {parts[1] for _,parts in selected}==set(expected),'DATASET_MANIFEST_COUNT')
 dataset=b.safe(candidate/'small-synthetic',candidate)
 b.need(dataset.is_dir(),'MISSING_DATASET')
 # Exact on-disk inventory; no ignored extra file, directory, or alias.
 entries=list(dataset.iterdir())
 b.need(len(entries)==12 and {p.name for p in entries}==set(expected),'DATASET_DISK_INVENTORY')
 result=[]
 for row,parts in selected:
  p=b.safe(candidate.joinpath(*parts),candidate)
  b.need(p.is_file() and p.stat().st_nlink==1,'MISSING_OR_LINKED_DATASET_FILE')
  b.need(p.stat().st_size==row['bytes'],'DATASET_SIZE')
  b.need(sha(p)==row['sha256'],'DATASET_HASH')
  result.append(dict(name=row['name'],sha256=row['sha256'],bytes=row['bytes']))
 b.need(sum(x['bytes'] for x in result)==786432,'DATASET_TOTAL_BYTES')
 return result
