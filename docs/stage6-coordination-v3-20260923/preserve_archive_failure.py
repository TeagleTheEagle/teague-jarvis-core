import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent
base=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS')
folders=list(base.glob('STAGE6 COORDINATION V3 FOCUSED 20260923 *'));assert len(folders)==1
folder=folders[0];records=[]
for p in sorted(folder.iterdir()):
 if p.is_file():records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with (R/'archive-verification-failure.json').open('x') as f:json.dump(dict(status='ARCHIVE_VERIFICATION_FAILED',reason='Manifest used Windows backslash in final-source member; zipfile normalized it to forward slash; lookup raised KeyError',error="There is no item named final-source/medium-checker\\application_authority.py in the archive",sourceChanged=False,preserved=records,correction='Normalize archive member names only; create a new archive, do not overwrite this one'),f,indent=2)
print(str(folder))
