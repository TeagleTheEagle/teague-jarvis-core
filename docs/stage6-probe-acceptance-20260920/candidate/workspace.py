"""Bounded D-only validation artifacts. No production paths or environment fallback."""
import os,pathlib,re,tempfile
BASE=pathlib.Path('D:/JARVIS-STAGE6-LIVE')
CODE=pathlib.Path(__file__).absolute().parent
def check_path(path):
 p=pathlib.Path(path).absolute()
 if '..' in p.parts or p.drive.upper()!='D:' or not p.is_relative_to(CODE):raise ValueError('D live workspace containment required')
 for q in (p,*p.parents):
  if q.exists() and (q.is_symlink() or q.is_junction()):raise ValueError('Reparse path forbidden')
  if q==BASE:break
 if not p.resolve().is_relative_to(CODE.resolve()):raise ValueError('Resolved escape')
 return p
if CODE.parent.parent!=BASE or CODE.name!='code' or not re.fullmatch('[a-f0-9]{32}',CODE.parent.name):raise RuntimeError('Must execute prepared D workspace copy')
check_path(CODE)
def run_dir(name):
 if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',name):raise ValueError('Invalid run ID')
 p=check_path(CODE/name)
 if not p.is_dir():raise ValueError('Prepared unique run required')
 return p
def new_run(name):
 if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',name):raise ValueError('Invalid run ID')
 p=check_path(CODE/name);p.mkdir(exist_ok=False);(p/'temp').mkdir();return p
def artifact(root,name):
 if pathlib.Path(name).name!=name or name in ('.','..') or ':' in name or '/' in name or '\\' in name:raise ValueError('Single artifact name required')
 return check_path(root/name)
def activate_temp(root):
 p=check_path(root/'temp')
 if not p.is_dir():raise ValueError('Prepared D temp required')
 os.environ['TEMP']=str(p);os.environ['TMP']=str(p);tempfile.tempdir=str(p)
 return p
