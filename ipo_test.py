import urllib.request, re, time

def get_upcoming_ipos():
    """Fetch top 5 upcoming IPOs from StockAnalysis"""
    try:
        url = "https://stockanalysis.com/ipo/calendar/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        
        ipos = []
        # Find IPO rows - company name, date, exchange
        rows = re.findall(r'<a href="/stock/[^"]+">([^<]+)</a>', html)
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', html)
        # Simple extraction - just grab company names near dates
        company_pattern = re.findall(r'<td[^>]*>\s*<a[^>]*>([^<]+)</a>', html)
        ipos = [(name.strip(),) for name in company_pattern[:5] if len(name.strip()) > 2 and len(name.strip()) < 30]
        
        return ipos[:5]
    except Exception as e:
        return []

print(get_upcoming_ipos())