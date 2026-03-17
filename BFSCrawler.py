import asyncio, sys, re, random
from playwright.async_api import async_playwright
from urllib.parse import urljoin

async def get_links(page, url): #método que pega todos os links da página
    links = await page.eval_on_selector_all("a[href]", "els => els.map(el => el.href)")
    return [urljoin(url, l).split('#')[0] for l in links if l.startswith('http')]

async def check_word(page, target): #método que busca a palavra-alvo na página
    if not target: return False
    text = await page.inner_text("body")
    return bool(re.search(rf"\b{re.escape(target)}\b", text, re.IGNORECASE))

async def run_crawl(start_url, target, link_limit=None):
    start_url = start_url.split('#')[0]
    queue, visited, count = [(start_url, 0)], {start_url}, 0 # fila, visitados e contador
    async with async_playwright() as p: # inicia o playwright
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page() # abre uma nova página
        while queue: # enquanto houver urls na fila
            url, depth = queue.pop(0) #pega a url e a profundidade da fila (FIFO)
            
            await asyncio.sleep(0.1)
            try:
                print(f"[{count+1}] Depth {depth} | Checking: {url}")
                await page.goto(url, wait_until="domcontentloaded") # vai para a url
                count += 1
                
                if await check_word(page, target): #checa se encontra a palavra
                    print(f"\nFound '{target}' at {url}\nPages: {count}, Depth: {depth}")
                    break
                
                new_links = [l for l in await get_links(page, url) if l not in visited] #pega os links da página
                if link_limit: random.shuffle(new_links) #embaralha os links caso haja limite de links definido
                
                if link_limit:
                    new_links = new_links[:link_limit] 
                
                for link in new_links: #adiciona os links na fila, incrementa a profundidade
                    visited.add(link)
                    queue.append((link, depth + 1))
            except: pass
        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2: 
        print("Usage: python BFSCrawler.py <url> [word] [link_limit]")
    else:
        url = sys.argv[1]
        word = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        asyncio.run(run_crawl(url, word, limit))
