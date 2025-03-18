import os
import requests
import tempfile
from pathlib import Path
from PIL import Image
from urllib.parse import urljoin

class MediaHandler:
    def __init__(self, wiki_url, wiki_token):
        self.wiki_url = wiki_url
        self.wiki_token = wiki_token
        self.headers = {'Authorization': f'Bearer {wiki_token}'}
        self.temp_dir = Path(tempfile.gettempdir()) / 'docflow_media'
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download_media(self, content, page_id):
        """Lädt alle Medien einer Wiki.js Seite herunter"""
        media_dir = self.temp_dir / str(page_id)
        media_dir.mkdir(parents=True, exist_ok=True)

        # Bilder im Markdown finden und herunterladen
        import re
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        def download_and_replace(match):
            alt_text = match.group(1)
            image_url = match.group(2)

            if not image_url.startswith(('http://', 'https://')):
                image_url = urljoin(self.wiki_url, f'/uploads/{image_url.lstrip("/")}')

            try:
                response = requests.get(image_url, headers=self.headers)
                if response.status_code == 200:
                    # Eindeutigen Dateinamen erstellen
                    image_name = Path(image_url).name
                    image_path = media_dir / image_name

                    # Bild speichern
                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    return f'![{alt_text}]({image_path})'
            except Exception as e:
                print(f"Fehler beim Download von {image_url}: {e}")
                return match.group(0)

        new_content = re.sub(image_pattern, download_and_replace, content)
        return new_content, media_dir
