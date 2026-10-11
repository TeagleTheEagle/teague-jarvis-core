"""Versioned TEST collector entry shim; fixed native RunCollector entry."""
import sys
from workspace import run_dir,activate_temp
from traced_collect_v3 import main
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root);sys.exit(main(root,sys.argv[2]))
