import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

visited_urls = set()
to_visit = []

async def fetch_info(page,url,base_domain):
    await page.goto(url)
    print(f"crawled : {url}")
    visited_urls.add(url)

    try:
        section = await page.query_selector("section.content-body.grid-75")
        if section:
            content = await section.inner_text()
        else:
            content = ""
    except Exception:
        content = ""
    
    links = await page.eval_on_selector_all('a','elements => elements.map(el => el.href)')

    for link in links:
        parsed = urlparse(link)
        if parsed.netloc == base_domain and link not in visited_urls and link not in to_visit:
            to_visit.append(link)
    
    return {'url':url,'content':content}

async def crawl(url,max_pages=5):
    global to_visit
    to_visit = [url]
    results = []
    base_domain = urlparse(url).netloc

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        while(to_visit and len(results) < max_pages):
            url = to_visit.pop(0)
            page = await context.new_page()
            try:
                doc = await fetch_info(page, url, base_domain)
                if doc['content'].strip():  # Save only if content found
                    results.append(doc)
            except Exception as e:
                print(f"Error on {url}: {e}")
            await page.close()

        await browser.close()
        
    return results
    
response = asyncio.run(crawl("https://docs.capillarytech.com/docs"))

# print(response)
with open("extracted_content.txt","w",encoding='utf-8') as f:
    for doc in response:
        f.write(doc.get('content')+'\n')