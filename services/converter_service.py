"""
DocFlow Konvertierungsdienst
Enthält Funktionen für die Konvertierung von Dokumenten
"""
import os
import subprocess
from datetime import datetime
from utils.file_utils import get_input_format, allowed_file
from utils.markdown_utils import clean_markdown_content
from config import OUTPUT_FORMAT_MAPPING  # Changed to absolute import

def convert_to_markdown(input_path, output_path):
    """Konvertiert eine Datei in Markdown mithilfe von pandoc"""
    input_format = get_input_format(input_path)

    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        subprocess.run([
            'pandoc',
            input_path,
            '-f', input_format,
            '-t', 'markdown',
            '-o', output_path
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Fehler bei der Konvertierung von {input_path}: {e}")
        return False

def export_pages_to_formats(page_paths, formats, session_id, result_folder, fetch_wikijs_page_content, log_debug, sanitize_filename):
    """
    Export Wiki.js pages to various document formats using Pandoc
    Args:
        page_paths: List of Wiki.js page paths to export
        formats: List of output formats
        session_id: Session ID for storing results
    Returns:
        tuple: (converted_files, failed_files)
    """
    log_debug(f"Starting export of {len(page_paths)} pages to formats: {', '.join(formats)}")

    # Create session directories
    export_dir = os.path.join(result_folder, session_id)
    os.makedirs(export_dir, exist_ok=True)

    converted_files = []
    failed_files = []

    for page_path in page_paths:
        try:
            # Get page content from Wiki.js
            log_debug(f"Fetching content for page: {page_path}")
            page_content, page_title = fetch_wikijs_page_content(page_path)

            if not page_content:
                log_debug(f"No content found for page: {page_path}", "error")
                failed_files.append(f"{page_path} (no content)")
                continue

            # If no title was returned, use the last part of the path
            if not page_title:
                page_title = os.path.basename(page_path)
            if not page_title:
                page_title = "untitled"

            # Sanitize the title for filename use
            safe_title = sanitize_filename(page_title)
            log_debug(f"Using title: {page_title} (sanitized as: {safe_title})")

            # Create temporary markdown file
            md_filename = f"{safe_title}.md"
            md_filepath = os.path.join(export_dir, md_filename)
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(page_content)

            # Convert to requested formats
            for output_format in formats:
                output_filename = f"{safe_title}.{output_format}"
                output_filepath = os.path.join(export_dir, output_filename)
                log_debug(f"Converting {page_path} to {output_format}")

                # Prepare command
                if output_format == "pdf":
                    cmd = [
                        'pandoc',
                        '-f', 'markdown',
                        '-t', 'pdf',
                        '-o', output_filepath,
                        md_filepath
                    ]
                else:
                    cmd = [
                        'pandoc',
                        '-f', 'markdown',
                        '-t', OUTPUT_FORMAT_MAPPING[output_format],
                        '-o', output_filepath,
                        md_filepath
                    ]

                # Execute conversion
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    converted_files.append(output_filename)
                    log_debug(f"Successfully converted {page_title} to {output_format}", "success")
                except subprocess.CalledProcessError as e:
                    log_debug(f"Pandoc error converting {page_title} to {output_format}: {e.stderr}", "error")
                    failed_files.append(f"{page_title} ({output_format})")
                except Exception as e:
                    log_debug(f"Error converting {page_title} to {output_format}: {str(e)}", "error")
                    failed_files.append(f"{page_title} ({output_format})")
        except Exception as e:
            log_debug(f"Unexpected error processing {page_path}: {str(e)}", "error")
            failed_files.append(page_path)

    return converted_files, failed_files
