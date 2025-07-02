"""
TXT to EPUB Converter - Public Version

This script converts plain text files from rewriter_pipeline.py into EPUB format, applying the same formatting and structure.
Injects rewritten chapters into the original EPUB structure, preserving the original metadata and formatting.

USAGE:
 1. Install dependencies:
    pip install beautifulsoup4

 3. Provide the required inputs below:
    - EPUB_FILE_PATH: Path to the original EPUB file.
    - OUTPUT_EPUB_PATH: Path where the new EPUB will be saved.
    - REWRITTEN_CHAPTERS_DIR: Directory containing rewritten chapters in text format.

 4. Run the script:
    python txt_to_xhtml.py

 5. Output will be saved in the specified OUTPUT_EPUB_PATH.

NOTE: Secrets and private file paths must be added by the user. If you use static type checkers (like mypy or some IDEs), you may see red errors or warnings about .contents, .clear, or .BeautifulSoup attributes/methods—these are false positives and can be safely ignored, as they do not affect the script's functionality or runtime.
"""

import os
import zipfile
import tempfile
import re
from bs4 import BeautifulSoup

EPUB_FILE_PATH = ""  # e.g., "{book_title}.epub"
OUTPUT_EPUB_PATH = ""  # e.g., "output_book.epub" - set the desired output file path here
REWRITTEN_CHAPTERS_DIR = "rewritten_novel" # default directory for rewritten chapters

def unzip_epub(epub_path, extract_to):
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def rezip_epub(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w') as epub:
        mimetype_path = os.path.join(folder_path, 'mimetype')
        epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)

        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, folder_path)
                if relative_path == 'mimetype':
                    continue
                epub.write(full_path, relative_path, compress_type=zipfile.ZIP_DEFLATED)

def smart_punctuation(text):
    # Simple replacements for smart quotes, ellipsis, em-dash
    text = text.replace('...', '…')
    text = text.replace('--', '—')
    # Curly quotes (basic)
    text = re.sub(r'"(.*?)"', r'“\1”', text)
    text = re.sub(r"'(.*?)'", r'‘\1’', text)
    return text

def parse_inline_markup(text):
    # Escape HTML special chars first
    text = (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    # Bold **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic *text* but NOT bold **text**
    # This regex avoids catching the ** by using lookarounds
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    
    # Apply smart punctuation
    text = smart_punctuation(text)
    return text

def process_line(line):
    line = line.strip()
    # Headings
    if re.match(r'#{1,6} ', line):
        hashes = re.match(r'(#+)', line).group(1)
        level = len(hashes)
        content = line[level+1:].strip()
        html_content = parse_inline_markup(content)
        return f"<h{level}>{html_content}</h{level}>"
    # Horizontal rules (*** or --- alone on line)
    if re.match(r'^\s*(\*\*\*|---)\s*$', line):
        return "<hr/>"
    # Otherwise paragraph
    html_content = parse_inline_markup(line)
    return f"<p>{html_content}</p>"

def replace_chapters(unzipped_dir):
    content_dir = os.path.join(unzipped_dir, 'EPUB', 'content')
    for file in os.listdir(REWRITTEN_CHAPTERS_DIR):
        if file.lower().endswith(".txt") and file.startswith("chapter_"):
            try:
                chapter_index = int(file.split("_")[1].split(".")[0])
            except (IndexError, ValueError):
                print(f"⚠️ Skipping: Unexpected filename format '{file}'")
                continue
            chapter_filename = f"Chapter{chapter_index}.xhtml"
            chapter_path = os.path.join(content_dir, chapter_filename)
            txt_path = os.path.join(REWRITTEN_CHAPTERS_DIR, file)

            if not os.path.exists(chapter_path):
                print(f"⚠️ Skipping: {chapter_filename} not found in EPUB")
                continue

            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Process lines and join them as XHTML fragments
            processed_lines = []
            paragraph_buffer = []
            def flush_paragraph():
                if paragraph_buffer:
                    paragraph_text = " ".join(paragraph_buffer).strip()
                    if paragraph_text:
                        processed_lines.append(process_line(paragraph_text))
                    paragraph_buffer.clear()

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    # blank line = paragraph break
                    flush_paragraph()
                else:
                    # If line is a HR or Heading on its own, flush buffer first
                    if re.match(r'#{1,6} ', stripped) or re.match(r'^\s*(\*\*\*|---)\s*$', stripped):
                        flush_paragraph()
                        processed_lines.append(process_line(stripped))
                    else:
                        paragraph_buffer.append(stripped)
            # Flush last paragraph
            flush_paragraph()

            with open(chapter_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "lxml")

            article_div = soup.find("div", {"id": "article"})
            if not article_div:
                print(f"Skipping: <div id='article'> not found in {chapter_filename}")
                continue

            article_div.clear()
            for fragment_html in processed_lines:
                fragment_soup = BeautifulSoup(fragment_html, "lxml")
                # Append all top-level tags from the fragment into article_div
                for tag in fragment_soup.body.contents:
                    # Insert a copy to avoid weird references
                    article_div.append(tag)
            
            with open(chapter_path, "w", encoding="utf-8") as f:
                # pretty print with minimal extra whitespace for EPUB
                f.write(str(soup))

            print(f"Updated: {chapter_filename}")

def main():
    """
    Unzips the original EPUB, replaces chapters with rewritten text files, rezips the EPUB, and saves the output.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        unzip_epub(EPUB_FILE_PATH, tmpdir)
        replace_chapters(tmpdir)
        rezip_epub(tmpdir, OUTPUT_EPUB_PATH)

    print(f"EPUB saved to {OUTPUT_EPUB_PATH}")
    
if __name__ == "__main__":
    main()
