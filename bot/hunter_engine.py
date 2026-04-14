import requests, re, time, datetime, os, random, socket, whois
from fake_useragent import UserAgent

class ContractorHunterCore:
    def __init__(self, delay=2):
        self.ua = UserAgent()
        self.delay = delay
        self.all_data = []
        self.stats = {'EMAIL': 0, 'PHONE': 0, 'SOCIAL': 0}

    def detect_cms(self, html):
        markers = {'WordPress': r'wp-content', '1C-Bitrix': r'bitrix/', 'Tilda': r'tilda\.ws', 'Joomla': r'Joomla!'}
        for name, pattern in markers.items():
            if re.search(pattern, html, re.I): return name
        return "Custom"

    def find_contractor(self, html):
        patterns = [r'meta name="author" content="([^"]+)"', r'(?:made by|developed by)[\s:]*<a[^>]*>([^<]+)</a>', r'<!--[\s]*dev(?:eloped)? by[\s:]*([^>]+)-->']
        for p in patterns:
            match = re.search(p, html, re.I)
            if match: return match.group(1).strip()[:40]
        return "Не определен"

    def scan_target(self, domain):
        target = domain.replace('http://', '').replace('https://', '').strip('/')
        try:
            ip = socket.gethostbyname(target)
            w = whois.whois(ip)
            country = (w.get('country') or '??').upper()
            if isinstance(country, list): country = country[0]
            isp = w.get('org') or w.get('as_name') or "Unknown ISP"
        except: ip, country, isp = "0.0.0.0", "??", "Unknown"

        site_info = {'domain': target, 'country': country, 'isp': isp, 'ip': ip, 'contacts': [], 'cms': 'Unknown', 'contractor': 'Unknown'}

        try:
            r = requests.get(f"https://{target}", timeout=10, headers={'User-Agent': self.ua.random})
            html = r.text
            site_info['cms'] = self.detect_cms(html)
            site_info['contractor'] = self.find_contractor(html)
            
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}', html)
            for e in set(emails): 
                site_info['contacts'].append(("EMAIL", e.lower()))
                self.stats['EMAIL'] += 1
            
            phones = re.findall(r'(?:\+7|8)[\s\(-]*\d{3}[\s\)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', html)
            for p in set(phones): 
                site_info['contacts'].append(("PHONE", p))
                self.stats['PHONE'] += 1
            
            self.all_data.append(site_info)
            return site_info
        except: return None

    def generate_html(self):
        fname = f"REPORT_{datetime.datetime.now().strftime('%d_%m_%H%M')}.html"
        blocks = ""
        for s in self.all_data:
            c_rows = "".join([f'<div style="margin:4px 0;"><span style="color:#58a6ff;">[{t}]</span> <span style="color:#d29922;">{v}</span></div>' for t,v in s['contacts']])
            blocks += f"""<div style="background:#161b22; border:1px solid #30363d; padding:15px; margin-bottom:15px; border-radius:6px; color:#c9d1d9; font-family:monospace;">
                <h3 style="color:#58a6ff; margin:0;">{s['domain']} <span style="float:right; background:#f85149; color:white; padding:2px 5px; font-size:10px;">{s['contractor']}</span></h3>
                <p>CMS: {s['cms']} | ISP: {s['isp']} ({s['country']})</p>
                <hr style="border:0; border-top:1px solid #30363d;">
                {c_rows if c_rows else 'Нет контактов'}
            </div>"""
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"<html><body style='background:#0d1117; padding:20px;'>{blocks}</body></html>")
        return fname
