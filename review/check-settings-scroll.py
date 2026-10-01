from pathlib import Path
p=Path('review/visual-overhaul/capture.py');s=p.read_text(encoding='utf-8');needle="  page.locator('[data-settings-category=Appearance]').click()";insert='''  page.locator('[data-settings-category=Developer]').click()
  page.locator('#settingsView').hover()
  page.mouse.wheel(0,800)
  page.wait_for_timeout(200)
  assert page.evaluate("document.getElementById('settingsView').scrollTop>0"),'Settings wheel scrolling failed'
  page.evaluate("document.getElementById('settingsView').scrollTop=0")
  page.get_by_text('Voice latency — development timings',exact=True).click()
  assert page.get_by_role('button',name='Refresh timing report').is_visible()
''';assert needle in s;s=s.replace(needle,insert+needle);p.write_text(s,encoding='utf-8')
