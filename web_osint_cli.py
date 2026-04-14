import requests
import re
import time
import datetime
import os
import random
import socket
import whois
from colorama import Fore, Style, init
from fake_useragent import UserAgent

init(autoreset=True)

class UltimateOsintV10:
    def __init__(self, delay=2, filter_country=None):
        self.ua = UserAgent()
        self.delay = delay
        self.filter_country = filter_country.upper() if filter_country else None
        self.all_data = []
        self.stats = {
            'countries': {},
            'cms': {},
            'contractors': {}, # Статистика по найденным студиям
            'contacts_total': {'EMAIL': 0, 'PHONE': 0, 'SOCIAL': 0}
        }
        self.proxies_list = self._load_proxies()

    def _load_proxies(self):
        if os.path.exists("proxy.txt"):
            with open("proxy.txt", "r") as f:
                return [line.strip() for line in f if line.strip()]
        return []

    def terminal_log(self, category, label, value):
        time_str = f"{Fore.LIGHTBLACK_EX}[{datetime.datetime.now().strftime('%H:%M:%S')}]{Fore.RESET}"
        print(f"{time_str} {Fore.CYAN}[{category}] {Fore.GREEN}{label} {Fore.RED}: {Fore.YELLOW}{value}")

    def find_contractor(self, html):
        """Интеллектуальный поиск названия студии-разработчика"""
        patterns = [
            r'meta name="author" content="([^"]+)"',
            r'(?:разработка сайта|создание сайта|made by|developed by)[\s:]*<a[^>]*>([^<]+)</a>',
            r'<!--[\s]*dev(?:eloped)? by[\s:]*([^>]+)-->',
            r'©[\s]*\d{4}[\s]*(?:by|студия|агентство)[\s]*([^<\n\r]+)',
            r'<(?:div|span|p)[^>]*class="[^"]*(?:copyright|dev|studio)[^"]*"[^>]*>([^<]+)</'
        ]
        for p in patterns:
            match = re.search(p, html, re.I)
            if match:
                name = match.group(1).strip()
                if len(name) < 50: return name
        return "Не определен"

    def detect_cms(self, html):
        markers = {'WordPress': r'wp-content', '1C-Bitrix': r'bitrix/', 'Tilda': r'tilda\.ws', 'Joomla': r'Joomla!'}
        for name, pattern in markers.items():
            if re.search(pattern, html, re.I): return name
        return "Custom"

    def scan_target(self, domain):
        target = domain.replace('http://', '').replace('https://', '').strip('/')
        try:
            ip = socket.gethostbyname(target)
            w = whois.whois(ip)
            country = (w.get('country') or '??').upper()
            if isinstance(country, list): country = country
            isp = w.get('org') or w.get('as_name') or "Unknown ISP"
        except: ip, country, isp = "0.0.0.0", "??", "Unknown"

        if self.filter_country and country != self.filter_country: return

        print(f"\n{Fore.WHITE}{Style.BRIGHT}{'='*10} ЦЕЛЬ: {target} {'='*10}")
        
        site_info = {'domain': target, 'country': country, 'isp': isp, 'ip': ip, 'contacts': [], 'cms': 'Unknown', 'contractor': 'Unknown'}

        try:
            r = requests.get(f"https://{target}", timeout=10, headers={'User-Agent': self.ua.random})
            html = r.text
            
            # Аналитика
            site_info['cms'] = self.detect_cms(html)
            site_info['contractor'] = self.find_contractor(html)
            
            self.terminal_log("TECH", "CMS", site_info['cms'])
            self.terminal_log("OSINT", "Подрядчик", site_info['contractor'])

            # Контакты
            for e in set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}', html)):
                site_info['contacts'].append(("EMAIL", e.lower())); self.stats['contacts_total']['EMAIL'] += 1
            
            for p in set(re.findall(r'(?:\+7|8)[\s\(-]*\d{3}[\s\)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}', html)):
                site_info['contacts'].append(("PHONE", p)); self.stats['contacts_total']['PHONE'] += 1

            # Статистика
            self.stats['countries'][country] = self.stats['countries'].get(country, 0) + 1
            self.stats['cms'][site_info['cms']] = self.stats['cms'].get(site_info['cms'], 0) + 1
            if site_info['contractor'] != "Не определен":
                self.stats['contractors'][site_info['contractor']] = self.stats['contractors'].get(site_info['contractor'], 0) + 1

            self.all_data.append(site_info)
        except: pass

    def generate_html(self):
        filename = f"CONTRACTOR_REPORT_{datetime.datetime.now().strftime('%d_%m_%H%M')}.html"
        
        # Сводные данные для дашборда
        cms_stat = "".join([f'<div class="pill">{c}: {n}</div>' for c, n in self.stats['cms'].items()])
        dev_stat = "".join([f'<li>{d}: {n}</li>' for d, n in sorted(self.stats['contractors'].items(), key=lambda x:x, reverse=True)[:5]])
        
        blocks = ""
        for s in self.all_data:
            blocks += f"""
            <div class="site-block">
                <div class="site-header">{s['domain']} <span class="tag-dev">{s['contractor']}</span></div>
                <div class="row"><span class="label">Движок</span><span class="sep">:</span><span class="val">{s['cms']}</span></div>
                <div class="row"><span class="label">Хостинг</span><span class="sep">:</span><span class="val">{s['isp']} ({s['country']})</span></div>
                <div class="sub-header">КОНТАКТЫ</div>
                {"".join([f'<div class="row"><span class="tag">[{t}]</span><span class="val">{v}</span></div>' for t,v in s['contacts']])}
            </div>"""

        style = """<style>
            body{background:#0d1117;color:#c9d1d9;font-family:Consolas,monospace;padding:40px;}
            .dash{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:40px;background:#161b22;padding:20px;border:1px solid #316dca;border-radius:8px;}
            .pill{background:#30363d;padding:4px 10px;border-radius:15px;margin:2px;display:inline-block;font-size:12px;color:#d29922;}
            .site-block{border:1px solid #30363d;background:#161b22;padding:20px;margin-bottom:20px;border-radius:6px;}
            .site-header{color:#58a6ff;font-size:18px;border-bottom:1px solid #30363d;padding-bottom:10px;margin-bottom:15px;}
            .tag-dev{float:right;background:#f85149;color:white;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:bold;}
            .row{display:flex;margin:4px 0;font-size:14px;}.label{color:#3fb950;min-width:140px;}.sep{color:#f85149;margin:0 10px;}.val{color:#d29922;}.tag{color:#58a6ff;width:85px;}
            h2{color:#8b949e;font-size:12px;text-transform:uppercase;margin-bottom:10px;}
        </style>"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<html><head><meta charset='UTF-8'>{style}</head><body><h1>CONTRACTOR HUNTER V10.0</h1><div class='dash'><div><h2>Движки</h2>{cms_stat}</div><div><h2>Топ подрядчиков</h2><ul>{dev_stat if dev_stat else 'Не найдены'}</ul></div><div><h2>Статистика</h2><p>Сайтов: {len(self.all_data)}</p><p>Emails: {self.stats['contacts_total']['EMAIL']}</p></div></div>{blocks}</body></html>")
        print(f"\n{Fore.GREEN}[SUCCESS] Финальный отчет: {filename}")

if __name__ == "__main__":
    print(f"{Fore.CYAN}{Style.BRIGHT}>>> CONTRACTOR HUNTER v10.0 [FINAL RELEASE]")
    target_in = input(f"{Fore.WHITE}Цель (.txt или домен): ").strip()
    hunter = UltimateOsintV10()
    targets = [l.strip() for l in open(target_in)] if os.path.isfile(target_in) else [target_in]
    for i, t in enumerate(targets):
        hunter.scan_target(t)
        if i < len(targets) - 1: time.sleep(2)
    hunter.generate_html()
