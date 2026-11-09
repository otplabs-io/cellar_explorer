# FROZEN RECORD of the script that made the delivered PDF. Not run by the build. Paths are from the original workspace.
from playwright.sync_api import sync_playwright
B='/tmp/claude-0/-home-claude/8b5e5abc-501d-54cd-8257-a48a145c8c87/scratchpad/build/'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':816,'height':2112},device_scale_factor=1.6)
    pg.goto('file://'+B+'proof.html'); pg.wait_for_timeout(800); pg.evaluate('document.fonts.ready')
    o=pg.evaluate('''()=>[...document.querySelectorAll('.pg > div')].map(r=>({sh:r.scrollHeight,ch:r.clientHeight,kids:[...r.children].map(c=>Math.round(c.getBoundingClientRect().bottom-r.getBoundingClientRect().top))}))''')
    print(o)
    pg.locator('.pg').nth(0).screenshot(path=B+'p1.png'); pg.locator('.pg').nth(1).screenshot(path=B+'p2.png')
    pg.pdf(path=B+'La-Boudriotte-2019.pdf',width='8.5in',height='11in',print_background=True,prefer_css_page_size=True)
    b.close()
