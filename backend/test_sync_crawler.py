from app.services.crawler_sync import WebCrawlerSync

def test():
    with WebCrawlerSync(timeout=30000) as crawler:
        data = crawler.crawl('https://example.com')
        print(f"Success! Title: {data['title']}")
        print(f"Status: {data['status_code']}")
        print(f"Load time: {data['load_time']:.2f}s")

if __name__ == "__main__":
    test()
