"""
Wiki.js API interaction functionality for DocFlow application
"""

import os
import requests
import traceback
from datetime import datetime
from urllib.parse import quote

def log_debug(message, log_type='info'):
    """Placeholder for log_debug function - will be replaced with app's function"""
    print(f"[{log_type.upper()}] {message}")

def test_connection(wikijs_url, wikijs_token, debug_logger=None):
    """Test connection to Wiki.js API"""
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    if not wikijs_url or not wikijs_token:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}

    try:
        # Use a simple query to list pages
        test_query = "{pages{list{id,title,path,contentType}}}"
        log_debug(f"Teste Wiki.js Verbindung zu: {wikijs_url}", "api")

        encoded_query = quote(test_query)

        headers = {
            'Authorization': f'Bearer {wikijs_token}'
        }
        log_debug(f"Sende GET-Anfrage an: {wikijs_url}/graphql/pages/list", "api")

        response = requests.get(
            f'{wikijs_url}/graphql/pages/list?query={encoded_query}',
            headers=headers
        )

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

        if 'data' in data and 'pages' in data['data'] and 'list' in data['data']['pages']:
            page_count = len(data['data']['pages']['list'])
            log_debug(f"Verbindung erfolgreich! {page_count} Seiten gefunden.", "success")
            return {'success': True, 'message': f'Verbindung zu Wiki.js erfolgreich hergestellt! {page_count} Seiten gefunden.'}
        else:
            log_debug("Unerwartetes Antwortformat von Wiki.js", "error")
            return {
                'success': False,
                'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'
            }

    except requests.exceptions.ConnectionError:
        log_debug(f"Verbindungsfehler: Server nicht erreichbar unter {wikijs_url}", "error")
        return {
            'success': False,
            'message': f'Verbindungsfehler: Server nicht erreichbar unter {wikijs_url}'
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

def get_directories(wikijs_url, wikijs_token, debug_logger=None):
    """Retrieves a list of all directories from Wiki.js"""
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    if not wikijs_url or not wikijs_token:
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
            'Authorization': f'Bearer {wikijs_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{wikijs_url}/graphql',
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
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'message': f'Error fetching directories: {str(e)}',
            'error_details': error_trace,
            'directories': []
        }

def fetch_pages(wikijs_url, wikijs_token, limit=100, debug_logger=None):
    """
    Retrieves a list of pages from Wiki.js
    Returns a tuple of (pages, error)
    """
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    if not wikijs_url or not wikijs_token:
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
            'Authorization': f'Bearer {wikijs_token}',
            'Content-Type': 'application/json'
        }

        log_debug(f"Fetching Wiki.js pages from: {wikijs_url}", "api")

        response = requests.post(
            f'{wikijs_url}/graphql',
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
        error_msg = f"Connection error: Could not connect to Wiki.js at {wikijs_url}"
        log_debug(error_msg, "error")
        return [], error_msg
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {str(e)}"
        log_debug(error_msg, "error")
        return [], error_msg
    except Exception as e:
        error_msg = f"Error fetching Wiki.js pages: {str(e)}"
        log_debug(error_msg, "error")
        log_debug(f"Traceback: {traceback.format_exc()}", "error")
        return [], error_msg

def fetch_page_content(page_path, wikijs_url, wikijs_token, debug_logger=None):
    """Fetch page content from Wiki.js API"""
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    log_debug(f"Fetching Wiki.js page content for path: {page_path}", "api")

    if not wikijs_url or not wikijs_token:
        log_debug("Wiki.js URL or token not configured", "error")
        return None, None

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {wikijs_token}'
    }

    # Step 1: First query to list all pages and find the matching one
    find_page_query = """
    query ListPages {
      pages {
        list {
          id
          path
          title
        }
      }
    }
    """

    try:
        log_debug(f"Step 1: Listing pages to find ID for path: {page_path}", "api")
        response = requests.post(
            f"{wikijs_url}/graphql",
            json={'query': find_page_query},
            headers=headers
        )

        response_data = response.json()

        if 'errors' in response_data:
            error_messages = ', '.join([error.get('message', 'Unknown error') for error in response_data['errors']])
            log_debug(f"GraphQL errors listing pages: {error_messages}", "error")
            return None, None

        # Extract pages from the response
        pages = response_data.get('data', {}).get('pages', {}).get('list', [])
        if not pages:
            log_debug(f"No pages found", "error")
            return None, None

        log_debug(f"Retrieved {len(pages)} pages, looking for path: {page_path}", "api")

        # Find the page with matching path
        matching_page = None
        for p in pages:
            if p.get('path') == page_path:
                matching_page = p
                break

        # If no exact match found
        if not matching_page:
            log_debug(f"No page found with path: {page_path}", "error")
            return None, None

        page_id = matching_page.get('id')
        title = matching_page.get('title')

        if not page_id:
            log_debug(f"Page found but has no ID for path: {page_path}", "error")
            return None, title

        log_debug(f"Found page ID: {page_id} for path: {page_path}", "success")

        # Step 2: Now get the content using the page ID
        content_query = """
        query GetPageContent($id: Int!) {
          pages {
            single(id: $id) {
              content
              title
              description
              path
              id
            }
          }
        }
        """

        content_variables = {
            'id': page_id
        }

        log_debug(f"Step 2: Fetching content for page ID: {page_id}", "api")
        content_response = requests.post(
            f"{wikijs_url}/graphql",
            json={'query': content_query, 'variables': content_variables},
            headers=headers
        )

        content_data = content_response.json()

        if 'errors' in content_data:
            error_messages = ', '.join([error.get('message', 'Unknown error') for error in content_data['errors']])
            log_debug(f"GraphQL errors fetching content: {error_messages}", "error")
            return None, title

        # Extract content from response
        page_data = content_data.get('data', {}).get('pages', {}).get('single')
        if not page_data:
            log_debug(f"No content data found for page ID: {page_id}", "error")
            return None, title

        content = page_data.get('content')
        # Update title if available in content response
        if page_data.get('title'):
            title = page_data.get('title')

        if not content:
            log_debug(f"Page found but content is empty. Page data: {page_data}", "warning")
            return None, title

        log_debug(f"Successfully fetched content for page: {title} ({len(content)} chars)", "success")
        return content, title

    except ValueError as json_err:
        log_debug(f"Failed to parse Wiki.js API response as JSON: {str(json_err)}", "error")
        log_debug(f"Raw response: {response.text[:200] if 'response' in locals() else 'No response available'}...", "error")
        return None, None

    except requests.exceptions.ConnectionError:
        log_debug(f"Connection error: Could not connect to Wiki.js at {wikijs_url}", "error")
        return None, None

    except requests.exceptions.HTTPError as http_err:
        log_debug(f"HTTP error from Wiki.js API: {http_err}", "error")
        return None, None

    except Exception as e:
        log_debug(f"Unexpected error while fetching page content: {str(e)}", "error")
        log_debug(f"Traceback: {traceback.format_exc()}", "error")
        return None, None

def upload_content(content, title, session_id, wikijs_url, wikijs_token, custom_path=None,
                   custom_title=None, username=None, default_folder=None, debug_logger=None,
                   external_url=None, sanitize_wikijs_path_fn=None, sanitize_wikijs_title_fn=None,
                   clean_markdown_content_fn=None):
    """Uploads a Markdown file to Wiki.js"""
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    if not sanitize_wikijs_path_fn or not sanitize_wikijs_title_fn or not clean_markdown_content_fn:
        log_debug("Required sanitization functions not provided", "error")
        return False, None

    if not wikijs_url or not wikijs_token:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_with_time = datetime.now().strftime("%Y-%m-%d-%H%M")

    # Remove .md extension from title if present
    title_without_extension = title
    if title.lower().endswith('.md'):
        title_without_extension = title[:-3]

    # Use custom title if provided, and sanitize it
    if custom_title and custom_title.strip():
        original_title = custom_title.strip()
        title_without_extension = sanitize_wikijs_title_fn(original_title)
        if original_title != title_without_extension:
            log_debug(f"Titel wurde sanitiert: '{original_title}' → '{title_without_extension}'", "info")
    else:
        title_without_extension = sanitize_wikijs_title_fn(title_without_extension)

    # For path use: Replace spaces with hyphens
    title_for_path = title_without_extension.replace(" ", "-")

    # Calculate default path with username and date
    safe_username = sanitize_wikijs_path_fn(username) if username else "anonymous"
    base_folder = "DocFlow"  # Default base folder
    default_path = f"{base_folder}/{safe_username}/{date_with_time}"
    sanitized_default_path = sanitize_wikijs_path_fn(default_path)

    # Use custom path if provided, otherwise use default path, and sanitize it
    if custom_path and custom_path.strip():
        # Remove leading and trailing slashes for consistency
        original_path = custom_path.strip().strip('/')
        path = sanitize_wikijs_path_fn(original_path)
        if original_path != path:
            log_debug(f"Pfad wurde sanitiert: '{original_path}' → '{path}'", "info")

        # If custom path is provided, use it directly
        # Add title only if it's not already part of the path
        if not path.endswith(f"/{title_for_path}") and not path.endswith(title_for_path):
            path = f"{path}/{title_for_path}"
            log_debug(f"Vollständiger Pfad mit Titel: {path}", "info")
    else:
        # If no custom path is provided...
        if default_folder and default_folder.strip():
            # If a default folder is selected, use it directly without username/date
            base_folder = sanitize_wikijs_path_fn(default_folder.strip())
            path = f"{base_folder}/{title_for_path}"
            log_debug(f"Verwende Standard-Ordner direkt: {path}", "info")
        else:
            # Create a default path with username and date+time
            path = f"{sanitized_default_path}/{title_for_path}"
            log_debug(f"Kein spezifischer Pfad angegeben. Verwende Standard-Pfad: {sanitized_default_path}/{title_for_path}", "info")
            log_debug(f"Info: Falls Sie keinen Pfad angeben, werden Ihre Dateien unter '{sanitized_default_path}/[Dateiname]' gespeichert.", "info")

    # Final check and sanitization of the path
    path = sanitize_wikijs_path_fn(path)

    # Clean the Markdown content of typical conversion artifacts
    cleaned_content = clean_markdown_content_fn(content)
    log_debug(f"Markdown-Inhalt bereinigt. {len(content) - len(cleaned_content)} Zeichen entfernt.", "info")

    log_debug(f"Starte Upload zu Wiki.js: {title_without_extension}", "api")
    log_debug(f"Ziel-Pfad: {path}", "api")

    headers = {
        'Authorization': f'Bearer {wikijs_token}',
        'Content-Type': 'application/json'
    }

    # Updated GraphQL mutation based on working curl example
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
        'content': cleaned_content,
        'description': f'Automatisch erstellt durch DocFlow am {timestamp}',
        'editor': 'markdown',
        'isPublished': True,
        'isPrivate': False,
        'locale': 'de',
        'path': path,
        'tags': ['DocFlow', 'Automatisch'],
        'title': title_without_extension
    }

    # Create full request payload for debugging
    request_payload = {
        'query': mutation,
        'variables': variables
    }

    # Log request details for debugging
    log_debug(f"Wiki.js URL: {wikijs_url}", "api")
    log_debug(f"GraphQL Mutation: {mutation.strip()}", "api")

    # Log variables with limited content for readability
    debug_variables = variables.copy()
    if len(content) > 200:
        debug_variables['content'] = content[:200] + '... [gekürzt]'
    log_debug(f"Variablen: {debug_variables}", "api")

    try:
        log_debug(f"Sende Wiki.js Request an: {wikijs_url}/graphql", "api")

        # POST with json payload for the mutation
        response = requests.post(
            f'{wikijs_url}/graphql',
            headers=headers,
            json=request_payload
        )

        log_debug(f"Status Code: {response.status_code}", "api")

        # Try to log the response body
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

        # Updated response verification based on curl example
        result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
        if result.get('succeeded'):
            # Extract page_id and actual path from response
            page = data.get('data', {}).get('pages', {}).get('create', {}).get('page', {})
            page_id = page.get('id')
            actual_path = page.get('path')

            # Construct full Wiki.js URL to the page using external URL instead of API URL
            wiki_url = f"{external_url}/{actual_path}" if external_url else f"{wikijs_url}/{actual_path}"
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
