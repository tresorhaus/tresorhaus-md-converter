#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocFlow - Markdown Converter for Wiki.js
Created by: Joachim Mild
Copyright (c) 2025 TresorHaus GmbH

Export functionality for DocFlow application
"""

import os
import subprocess
import zipfile
import io
from datetime import datetime

def log_debug(message, log_type='info'):
    """Placeholder for log_debug function - will be replaced with app's function"""
    print(f"[{log_type.upper()}] {message}")

def export_pages_to_formats(page_paths, formats, session_id, result_folder, wikijs_url, wikijs_token,
                            output_format_mapping, sanitize_filename_fn, fetch_page_content_fn, debug_logger=None):
    """
    Export Wiki.js pages to various document formats using Pandoc

    Args:
        page_paths: List of Wiki.js page paths to export
        formats: List of output formats
        session_id: Session ID for storing results
        result_folder: Folder for storing results
        wikijs_url: Wiki.js URL
        wikijs_token: Wiki.js API token
        output_format_mapping: Mapping of formats to pandoc format strings
        sanitize_filename_fn: Function to sanitize filenames
        fetch_page_content_fn: Function to fetch page content
        debug_logger: Debug logger function

    Returns:
        tuple: (converted_files, failed_files, debug_data)
    """
    global log_debug
    if debug_logger:
        log_debug = debug_logger

    log_debug(f"Starting export of {len(page_paths)} pages to formats: {', '.join(formats)}")

    # Create session directories
    export_dir = os.path.join(result_folder, session_id)
    os.makedirs(export_dir, exist_ok=True)

    converted_files = []
    failed_files = []
    debug_data = {}

    for page_path in page_paths:
        try:
            # Get page content from Wiki.js
            log_debug(f"Fetching content for page: {page_path}")
            page_content, page_title = fetch_page_content_fn(page_path, wikijs_url, wikijs_token, debug_logger)

            # Store debug data for this page
            debug_data[page_path] = {
                'title': page_title,
                'content_length': len(page_content) if page_content else 0,
                'has_content': bool(page_content)
            }

            if not page_content:
                error_msg = "No content found"
                log_debug(f"No content found for page: {page_path}", "error")
                failed_files.append(f"{page_path} (no content)")
                continue

            # If no title was returned, use the last part of the path
            if not page_title:
                page_title = os.path.basename(page_path)

            if not page_title:
                page_title = "untitled"

            # Sanitize the title for filename use
            safe_title = sanitize_filename_fn(page_title)
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
                        '-t', output_format_mapping[output_format],
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

    return converted_files, failed_files, debug_data

def create_zip_file(session_id, result_folder):
    """Creates a ZIP file with all converted Markdown files"""
    result_dir = os.path.join(result_folder, session_id)
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, result_dir)
                zf.write(file_path, rel_path)

    memory_file.seek(0)
    return memory_file

def create_exported_zip(session_id, result_folder):
    """Creates a ZIP file with all exported files"""
    session_result_dir = os.path.join(result_folder, session_id)

    if not os.path.exists(session_result_dir):
        return None

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(session_result_dir):
            for file in files:
                if file.endswith(('.md', '.docx', '.odt', '.rtf', '.pdf', '.html', '.tex', '.epub', '.pptx')):
                    zipf.write(
                        os.path.join(root, file),
                        os.path.basename(file)
                    )

    memory_file.seek(0)
    return memory_file
