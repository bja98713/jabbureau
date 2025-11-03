import os
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

from django.conf import settings
from django.core.management.base import BaseCommand

SOURCE_URL = "https://angh.net/pratique-2/fiches-information-patient/"

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'a':
            return
        href = dict(attrs).get('href')
        if href:
            self.links.append(href)

class Command(BaseCommand):
    help = "Télécharge les fiches d'information patient (PDF) depuis ANGH dans static/fiches/."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Fetching page: {SOURCE_URL}"))
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        parser = LinkExtractor()
        parser.feed(html)

        pdf_links = []
        for href in parser.links:
            if href.lower().endswith('.pdf'):
                pdf_links.append(urllib.parse.urljoin(SOURCE_URL, href))

        if not pdf_links:
            self.stdout.write(self.style.WARNING("Aucun lien PDF détecté sur la page.") )
            return

        out_dir = os.path.join(settings.BASE_DIR, 'static', 'fiches')
        os.makedirs(out_dir, exist_ok=True)

        def sanitize(name: str) -> str:
            # Simple sanitize: keep basename and strip query string; replace spaces
            name = name.split('?')[0]
            name = os.path.basename(name)
            return re.sub(r'\s+', '_', name)

        for url in sorted(set(pdf_links)):
            fname = sanitize(url)
            dest_path = os.path.join(out_dir, fname)
            if os.path.exists(dest_path):
                self.stdout.write(f"Skip (exists): {fname}")
                continue
            self.stdout.write(f"Downloading: {url} → {fname}")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as r, open(dest_path, 'wb') as f:
                    f.write(r.read())
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur sur {url}: {e}"))

        self.stdout.write(self.style.SUCCESS("Fini. Vous pouvez retrouver les PDFs dans static/fiches/"))
