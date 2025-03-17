"""
DocFlow Wiki.js Service
Enthält Funktionen für die Integration mit Wiki.js
"""
import requests
import urllib.parse
from datetime import datetime
import traceback
from utils.markdown_utils import clean_markdown_content, sanitize_wikijs_path, sanitize_wikijs_title
from config import WIKIJS_URL, WIKIJS_TOKEN, WIKIJS_EXTERNAL_URL

def upload_to_wikijs(content, title, session_id, custom_path=None, custom_title=None, username=None, default_folder=None, log_debug=None):
    """Lädt eine Markdown-Datei in Wiki.js hoch"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_with_time = datetime.now().strftime("%Y-%m-%d-%H%M")

    # Entferne .md Erweiterung aus dem Titel wenn vorhanden
    title_without_extension = title
    if title.lower().endswith('.md'):
        title_without_extension = title[:-3]

    # Verwende den benutzerdefinierten Titel, wenn angegeben, und sanitiere ihn
    if custom_title and custom_title.strip():
        original_title = custom_title.strip()
        title_without_extension = sanitize_wikijs_title(original_title)
        if original_title != title_without_extension:
            log_debug(f"Titel wurde sanitiert: '{original_title}' → '{title_without_extension}'", "info")
    else:
        title_without_extension = sanitize_wikijs_title(title_without_extension)

    # Für die Verwendung im Pfad: Ersetze Leerzeichen mit Bindestrichen
    title_for_path = title_without_extension.replace(" ", "-")

    # Berechnete Standardpfad mit Username und Datum
    safe_username = sanitize_wikijs_path(username) if username else "anonymous"
    base_folder = "DocFlow"  # Standard-Basis-Ordner
    default_path = f"{base_folder}/{safe_username}/{date_with_time}"
    sanitized_default_path = sanitize_wikijs_path(default_path)

    # Verwende den benutzerdefinierten Pfad, wenn angegeben, sonst den Standard-Pfad, und sanitiere ihn
    if custom_path and custom_path.strip():
        # Entferne führende und folgende Schrägstriche für Konsistenz
        original_path = custom_path.strip().strip('/')
        path = sanitize_wikijs_path(original_path)
        if original_path != path:
            log_debug(f"Pfad wurde sanitiert: '{original_path}' → '{path}'", "info")
        # Wenn ein benutzerdefinierter Pfad angegeben ist, verwende diesen direkt
        # Füge nur den Titel hinzu, wenn er nicht bereits Teil des Pfades ist
        if not path.endswith(f"/{title_for_path}") and not path.endswith(title_for_path):
            path = f"{path}/{title_for_path}"
            log_debug(f"Vollständiger Pfad mit Titel: {path}", "info")
    else:
        # Wenn kein benutzerdefinierter Pfad angegeben ist...
        if default_folder and default_folder.strip():
            # Wenn ein Standard-Ordner ausgewählt wurde, verwende diesen direkt ohne Username/Datum
            base_folder = sanitize_wikijs_path(default_folder.strip())
            path = f"{base_folder}/{title_for_path}"
            log_debug(f"Verwende Standard-Ordner direkt: {path}", "info")
        else:
            # Erstelle einen Standard-Pfad mit Benutzernamen und Datum+Uhrzeit
            path = f"{sanitized_default_path}/{title_for_path}"
            log_debug(f"Kein spezifischer Pfad angegeben. Verwende Standard-Pfad: {sanitized_default_path}/{title_for_path}", "info")
            log_debug(f"Info: Falls Sie keinen Pfad angeben, werden Ihre Dateien unter '{sanitized_default_path}/[Dateiname]' gespeichert.", "info")

    # Endgültige Prüfung und Sanitierung des Pfades
    path = sanitize_wikijs_path(path)

    # Bereinige den Markdown-Inhalt von typischen Konvertierungsartefakten
    cleaned_content = clean_markdown_content(content)
    log_debug(f"Markdown-Inhalt bereinigt. {len(content) - len(cleaned_content)} Zeichen entfernt.", "info")

    log_debug(f"Starte Upload zu Wiki.js: {title_without_extension}", "api")
    log_debug(f"Ziel-Pfad: {path}", "api")

    headers = {
        'Authorization': f'Bearer {WIKIJS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Aktualisierte GraphQL mutation basierend auf dem funktionierenden curl-Beispiel
    mutation = """
    mutation Page ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
      pages {
        create (content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
          responseResult {
            succeeded,
            errorCode,
            slug,
            message
          },
          page {
            id,
            path,
            title
          }
        }
      }
    }
    """

    variables = {
        'content': cleaned_content,  # Verwende den bereinigten Inhalt statt des Originals
        'description': f'Automatisch erstellt durch  DocFlow am {timestamp}',
        'editor': 'markdown',
        'isPublished': True,
        'isPrivate': False,  # Hinzugefügt entsprechend dem curl-Beispiel
        'locale': 'de',
        'path': path,
        'tags': ['DocFlow', 'Automatisch'],
        'title': title_without_extension
    }

    # Erstelle die vollständige Request-Payload für Debug-Zwecke
    request_payload = {
        'query': mutation,
        'variables': variables
    }

    # Log vollständige Request-Details für Debugging
    log_debug(f"Wiki.js URL: {WIKIJS_URL}", "api")
    log_debug(f"GraphQL Mutation: {mutation.strip()}", "api")

    # Logge Variablen mit limitiertem Content für Übersichtlichkeit
    debug_variables = variables.copy()
    if len(content) > 200:
        debug_variables['content'] = content[:200] + '... [gekürzt]'
    log_debug(f"Variablen: {debug_variables}", "api")

    # Logge die ersten 200 Zeichen des Inhalts
    log_debug(f"Inhalt (gekürzt): {content[:200]}...", "api")

    # Logge die vollständige Länge des Inhalts
    log_debug(f"Gesamte Inhaltslänge: {len(content)} Zeichen", "api")

    try:
        log_debug(f"Sende Wiki.js Request an: {WIKIJS_URL}/graphql", "api")

        # POST mit json payload für die Mutation
        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json=request_payload
        )

        log_debug(f"Status Code: {response.status_code}", "api")

        # Versuchen, den Response-Body zu loggen
        try:
            response_text = response.text
            if len(response_text) > 500:
                log_debug(f"Response (gekürzt): {response_text[:500]}...", "api")
            else:
                log_debug(f"Response: {response_text}", "api")
        except:
            log_debug("Konnte Response-Body nicht lesen", "error")

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            log_debug(f"GraphQL Fehler: {error_msg}", "error")
            return False, None

        # Aktualisierte Überprüfung der Antwort basierend auf dem curl-Beispiel
        result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})

        if result.get('succeeded'):
            # Extrahiere die page_id und den tatsächlichen Pfad aus der Antwort
            page = data.get('data', {}).get('pages', {}).get('create', {}).get('page', {})
            page_id = page.get('id')
            actual_path = page.get('path')

            # Konstruiere die vollständige Wiki.js URL zur Seite mit der externen URL statt der API-URL
            wiki_url = f"{WIKIJS_EXTERNAL_URL}/{actual_path}"
            log_debug(f"Wiki.js Seite erfolgreich erstellt: {wiki_url} (ID: {page_id})", "success")
            return True, wiki_url
        else:
            error_message = result.get('message', 'Unbekannter Fehler')
            error_code = result.get('errorCode', 'Kein Code')
            log_debug(f"Wiki.js Fehler: {error_message} (Code: {error_code})", "error")
            return False, None
    except Exception as e:
        log_debug(f"Fehler beim Upload zu Wiki.js: {str(e)}", "error")
        log_debug(f"Exception Details: {type(e).__name__}", "error")
        log_debug(f"Traceback: {traceback.format_exc()}", "error")
        return False, None

def test_wikijs_connection(log_debug):
    """Testet die Verbindung zu Wiki.js"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}

    # Test connection using pages list query
    try:
        # Use a simple query to list pages
        test_query = "{pages{list{id,title,path,contentType}}}"
        log_debug(f"Teste Wiki.js Verbindung zu: {WIKIJS_URL}", "api")

        # URL encode the query parameter
        encoded_query = urllib.parse.quote(test_query)
        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}'
        }

        log_debug(f"Sende GET-Anfrage an: {WIKIJS_URL}/graphql/pages/list", "api")

        # Use GET request to the pages list endpoint with query as URL parameter
        response = requests.get(
            f'{WIKIJS_URL}/graphql/pages/list?query={encoded_query}',
            headers=headers
        )

        # Log detailed debug info
        log_debug(f"Status Code: {response.status_code}", "api")
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unbekannter GraphQL-Fehler')
            log_debug(f"API-Fehler: {error_msg}", "error")
            return {
                'success': False,
                'message': f"API-Fehler: {error_msg}\nBitte überprüfen Sie den API-Token."
            }

        # Check if we got a valid response with pages data
        if 'data' in data and 'pages' in data['data'] and 'list' in data['data']['pages']:
            page_count = len(data['data']['pages']['list'])
            log_debug(f"Verbindung erfolgreich! {page_count} Seiten gefunden.", "success")
            return {'success': True, 'message': f'Verbindung zu Wiki.js erfolgreich hergestellt! {page_count} Seiten gef
unden.'}
        else:
            log_debug("Unerwartetes Antwortformat von Wiki.js", "error")
            return {
                'success': False,
                'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'
            }
    except requests.exceptions.ConnectionError:
        log_debug(f"Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}", "error")
        return {
            'success': False,
            'message': f'Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}'
        }
    except requests.exceptions.HTTPError as e:
        log_debug(f"HTTP-Fehler {e.response.status_code}: {e.response.text}", "error")
        if e.response.status_code == 401:
            return {
                'success': False,
                'message': 'Authentifizierungsfehler: Ungültiger API-Token'
            }
        elif e.response.status_code == 400:
            return {
                'success': False,
                'message': 'API-Fehler: Ungültige Anfrage. Bitte überprüfen Sie die Wiki.js-URL und den API-Token'
            }
        return {
            'success': False,
            'message': f'HTTP-Fehler {e.response.status_code}: {e.response.text}'
        }
    except Exception as e:
        log_debug(f"Unerwarteter Fehler: {str(e)}", "error")
        return {
            'success': False,
            'message': f'Unerwarteter Fehler: {str(e)}\nBitte überprüfen Sie die Konsole für weitere Details.'
        }

def get_wikijs_directories():
    """Retrieves a list of all directories from Wiki.js"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert', 'directories': []}

    try:
        # GraphQL query to get all pages which will be used to extract unique directories
        query = """
        {
          pages {
            list {
              path
            }
          }
        }
        """

        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json={'query': query}
        )

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            return {'success': False, 'message': f'GraphQL Error: {error_msg}', 'directories': []}

        # Extract all paths from the pages
        pages = data.get('data', {}).get('pages', {}).get('list', [])
        all_paths = [page['path'] for page in pages if 'path' in page]

        # Extract unique directories from paths
        directories = set()
        for path in all_paths:
            # Split the path and reconstruct directories
            parts = path.split('/')
            for i in range(1, len(parts)):
                directories.add('/'.join(parts[:i]))

        # Convert set to list and sort
        directory_list = sorted(list(directories))

        # Add root directory if it doesn't exist
        if '' not in directory_list:
            directory_list.insert(0, '')

        return {'success': True, 'directories': directory_list}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'message': f'Error fetching directories: {str(e)}',
            'error_details': error_trace,
            'directories': []
        }

def fetch_wikijs_pages(limit=100, log_debug=None):
    """
    Retrieves a list of pages from Wiki.js
    Returns a tuple of (pages, error)
    """
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        return [], "Wiki.js URL oder Token nicht konfiguriert"

    try:
        # GraphQL query to get all pages with id, title, path, and contentType
        query = f"""
        {{
          pages {{
            list(limit: {limit}) {{
              id
              title
              path
              contentType
            }}
          }}
        }}
        """

        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}',
            'Content-Type': 'application/json'
        }

        log_debug(f"Fetching Wiki.js pages from: {WIKIJS_URL}", "api")

        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json={'query': query}
        )

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            log_debug(f"GraphQL Error when fetching pages: {error_msg}", "error")
            return [], f"GraphQL Error: {error_msg}"

        # Extract pages from response
        pages = data.get('data', {}).get('pages', {}).get('list', [])
        log_debug(f"Successfully fetched {len(pages)} pages from Wiki.js", "success")

        # Filter out only markdown content type pages
        markdown_pages = [page for page in pages if page.get('contentType') == 'markdown']

        return markdown_pages, None
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: Could not connect to Wiki.js at {WIKIJS_URL}"
        log_debug(error_msg, "error")
        return [], error_msg
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {str(e)}"
        log_debug(error_msg, "error")
        return [], error_msg
    except Exception as e:
        error_msg = f"Error fetching Wiki.js pages: {str(e)}"
        log_debug(error_msg, "error")
        import traceback
        log_debug(f"Traceback: {traceback.format_exc()}", "error")
        return [], error_msg

def fetch_wikijs_page_content(page_path, log_debug=None):
    """Fetch page content from Wiki.js API"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        log_debug("Wiki.js URL or token not configured", "error")
        return None, None

    log_debug(f"Fetching content for page: {page_path}")

    # GraphQL query to get page content and title
    query = """
    query ($path: String!) {
        pages {
            single(path: $path) {
                content
                title
            }
        }
    }
    """

    variables = {
        "path": page_path
    }

    headers = {
        "Authorization": f"Bearer {WIKIJS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{WIKIJS_URL}/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )

        if response.status_code != 200:
            log_debug(f"Wiki.js API error: {response.status_code} - {response.text}", "error")
            return None, None

        data = response.json()

        # Check for errors in the response
        if "errors" in data:
            log_debug(f"Wiki.js GraphQL error: {data['errors']}", "error")
            return None, None

        # Extract page content and title
        if data.get("data") and data["data"].get("pages") and data["data"]["pages"].get("single"):
            page_data = data["data"]["pages"]["single"]
            content = page_data.get("content", "")
            title = page_data.get("title", "")
            return content, title
        else:
            log_debug(f"No content found for page: {page_path}", "error")
            return None, None
    except Exception as e:
        log_debug(f"Error fetching page content: {str(e)}", "error")
        return None, None
