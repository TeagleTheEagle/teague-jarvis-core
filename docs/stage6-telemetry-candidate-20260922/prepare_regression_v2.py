from pathlib import Path
R=Path(__file__).parent;s=(R/'validate_preparation.py').read_text()
s=s.replace("C/'validation'","C/'validation-v2'").replace("C/'fixtures'","C/'fixtures-v2'").replace("R/'legacy-83-execution.json'","R/'legacy-83-execution-v2.json'")
needle="(V/'legacy_tests.py').write_text(driver,encoding='utf8')"
assert s.count(needle)==1
s=s.replace(needle,"driver=driver.replace(\"R.parent/'test-results-location.json'\",\"R/'test-results-location.json'\")\n"+needle)
with (R/'validate_preparation_v2.py').open('x') as f:f.write(s)
