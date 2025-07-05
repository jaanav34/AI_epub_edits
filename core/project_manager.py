# core/project_manager.py
import os
import json
import shutil
import zipfile
import re
from typing import Optional
from bs4 import BeautifulSoup
from ebooklib import epub
from tqdm import tqdm
from core.config_manager import ConfigManager  # Import ConfigManager

PROJECTS_BASE_DIR = "projects"
SOURCE_DIR = "0_source"
EXTRACTED_DIR = "1_extracted"
REWRITTEN_TXT_DIR = "2_rewritten_txt"
FINAL_EPUB_DIR = "3_final_epub"
PROJECT_CONFIG_FILE = "project_config.json"
PROJECT_STATE_FILE = "project_state.json"
CONTEXT_GLOSSARY_FILE = "context_glossary.json"
LOG_FILE = "rewriter.log"
PROMPT_LOG_FILE = "prompt_log.txt"

class ProjectManager:
    """Handles the creation, loading, state, and file operations for a single rewrite project."""
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_dir = os.path.join(PROJECTS_BASE_DIR, self.project_name)
        self.source_dir = os.path.join(self.project_dir, SOURCE_DIR)
        self.extracted_dir = os.path.join(self.project_dir, EXTRACTED_DIR)
        self.rewritten_txt_dir = os.path.join(self.project_dir, REWRITTEN_TXT_DIR)
        self.final_epub_dir = os.path.join(self.project_dir, FINAL_EPUB_DIR)
        self.config_path = os.path.join(self.project_dir, PROJECT_CONFIG_FILE)
        self.state_path = os.path.join(self.project_dir, PROJECT_STATE_FILE)
        self.glossary_path = os.path.join(self.project_dir, CONTEXT_GLOSSARY_FILE)
        self.log_path = os.path.join(self.project_dir, LOG_FILE)
        self.prompt_log_path = os.path.join(self.project_dir, PROMPT_LOG_FILE)

    def project_exists(self) -> bool:
        return os.path.isdir(self.project_dir)

    def create_new_project(self, source_epub_path: str, style_ref_path: str):
        """Creates the full directory structure for a new project."""
        if self.project_exists():
            print(f"Warning: Project '{self.project_name}' already exists. Overwriting config and source files.")
        
        # Create all directories
        for path in [self.project_dir, self.source_dir, self.extracted_dir, self.rewritten_txt_dir, self.final_epub_dir]:
            os.makedirs(path, exist_ok=True)

        # Copy source EPUB
        epub_filename = os.path.basename(source_epub_path)
        shutil.copy(source_epub_path, os.path.join(self.source_dir, epub_filename))
        
        # Read style reference
        with open(style_ref_path, 'r', encoding='utf-8') as f:
            style_reference_text = f.read()

        # Create project config
        project_config = {
            "projectName": self.project_name,
            "sourceEpub": epub_filename,
            "styleReferenceText": style_reference_text,
            "overrides": {}
        }
        self.save_config(project_config)
        
        # Unzip and initialize state
        self._unzip_source_epub()
        chapters = self._extract_chapters_from_epub()
        self._initialize_project_state(chapters)

    def load_config(self) -> dict:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_config(self, config_data: dict):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

    def load_state(self) -> dict:
        if not os.path.exists(self.state_path):
            return {}
        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_state(self, state_data: dict):
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)

    def _unzip_source_epub(self):
        """Unzips the source EPUB into the extracted directory and patches broken cover metadata."""
        config = self.load_config()
        source_path = os.path.join(self.source_dir, config['sourceEpub'])

        with zipfile.ZipFile(source_path, 'r') as zip_ref:
            zip_ref.extractall(self.extracted_dir)
        print(f"EPUB unzipped to {self.extracted_dir}")

        # Patch the OPF to fix broken cover.jpg references globally
        self._patch_opf_cover_extension(self.extracted_dir)

    def _patch_opf_cover_extension(self, base_dir):
        """Fixes .jpg to .png in OPF file inside extracted EPUB."""
        opf_path = None
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".opf"):
                    opf_path = os.path.join(root, file)
                    break
            if opf_path:
                break

        if opf_path and os.path.exists(opf_path):
            with open(opf_path, 'r', encoding='utf-8') as f:
                opf_content = f.read()
            patched = re.sub(r'\.jpg\b', '.png', opf_content, flags=re.IGNORECASE)
            with open(opf_path, 'w', encoding='utf-8') as f:
                f.write(patched)
            print("✅ Patched .jpg → .png in OPF.")
        else:
            print("⚠️ OPF file not found for patching.")

    def _initialize_project_state(self, chapters: list):
        """Creates the initial state file based on extracted chapters."""
        state = {
            "projectName": self.project_name,
            "totalChapters": len(chapters),
            "chapters": {}
        }
        for i, chap in enumerate(chapters):
            state["chapters"][str(i + 1)] = {
                "id": chap['id'],
                "title": chap['title'],
                "status": "pending",
                "original_text": chap['original_text'],
                "rewritten_text_file": f"chapter_{i+1:03d}.txt",
                "summary": "",
                "error": None
            }
        self.save_state(state)
        print(f"Project state initialized with {len(chapters)} chapters.")

    
    def _html_to_text(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return re.sub(r'\n\s*\n', '\n\n', text).strip()
    
    def clean_epub_metadata(self, epub_path: str, cleaned_epub_path: str) -> str:
        """
        Unzips the EPUB, fixes broken .jpg cover references in the OPF file, and re-zips it.
        Returns the path to the cleaned EPUB.
        """
        import zipfile
        import tempfile
        import shutil
        import re
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Try to find the OPF file (usually under EPUB/content.opf or similar)
            opf_path = None
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    if file.endswith(".opf"):
                        opf_path = os.path.join(root, file)
                        break
                if opf_path:
                    break

            if not opf_path:
                raise FileNotFoundError("Could not find OPF file in EPUB structure.")

            # Read, patch, and write back the OPF
            with open(opf_path, 'r', encoding='utf-8') as f:
                opf_content = f.read()

            # Automatically replace all .jpg references with .png (for cover images)
            opf_content = re.sub(r'\.jpg\b', '.png', opf_content, flags=re.IGNORECASE)

            with open(opf_path, 'w', encoding='utf-8') as f:
                f.write(opf_content)

            # Create the cleaned EPUB
            with zipfile.ZipFile(cleaned_epub_path, 'w') as zip_write:
                for foldername, _, filenames in os.walk(tmpdir):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        arcname = os.path.relpath(file_path, tmpdir)
                        compress_type = zipfile.ZIP_STORED if arcname == 'mimetype' else zipfile.ZIP_DEFLATED
                        zip_write.write(file_path, arcname, compress_type=compress_type)

        return cleaned_epub_path

    
    def _extract_chapters_from_epub(self) -> list:
        """Reads the source EPUB, cleans metadata, and extracts chapter data (with correct spine alignment)."""
        epub_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.epub')]
        if not epub_files:
            raise FileNotFoundError("No EPUB file found in source directory.")
        source_epub_path = os.path.join(self.source_dir, epub_files[0])

        cleaned_epub_path = os.path.join(self.project_dir, "cleaned.epub")
        self.clean_epub_metadata(source_epub_path, cleaned_epub_path)

        try:
            book = epub.read_epub(cleaned_epub_path, options={'ignore_ncx': True, 'ignore_missing_files': True})

            # Map from OPF id to EpubHtml item using the book's manifest
            id_to_item = {}
            for item in book.items:
                if isinstance(item, epub.EpubHtml):
                    id_to_item[item.get_id()] = item

            spine_ids = [item_id for item_id, _ in book.spine]

            chapters = []
            for i, idref in enumerate(spine_ids):
                item = id_to_item.get(idref)
                if not item:
                    print(f"⚠️ Warning: ID '{idref}' from spine not found in EpubHtml items.")
                    continue

                html_content = item.get_content().decode('utf-8', 'ignore')
                text_content = self._html_to_text(html_content)

                soup = BeautifulSoup(html_content, 'html.parser')
                title_tag = soup.find(['h1', 'h2', 'h3'])
                title = title_tag.get_text(strip=True) if title_tag else f"Chapter {i+1}"

                chapters.append({
                    "title": title,
                    "original_text": text_content,
                    "id": item.get_name()
                })

            if chapters:
                print(f"✅ Extracted {len(chapters)} chapters using ebooklib (spine-driven).")
                return chapters
            else:
                print("⚠️ No chapters found via ebooklib. Falling back to raw XHTML scan.")
                return self._fallback_extract_chapters()
        except Exception as e:
            print(f"⚠️ Failed to extract chapters with ebooklib: {e}")
            print("👉 Falling back to raw XHTML scan.")
            return self._fallback_extract_chapters()


                
    def _fallback_extract_chapters(self) -> list:
        chapters = []
        index = 0

        for root, _, files in os.walk(self.extracted_dir):
            for file in sorted(files):
                if file.lower().endswith('.xhtml') and 'chapter' in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        text_content = self._html_to_text(html_content)
                        title_tag = soup.find(['h1', 'h2', 'h3'])
                        title = title_tag.get_text(strip=True) if title_tag else f"Chapter {index + 1}"
                        
                        chapters.append({
                            "title": title,
                            "original_text": text_content,
                            "id": os.path.relpath(file_path, self.extracted_dir)
                        })
                        index += 1
                    except Exception as e:
                        print(f"Failed to parse chapter {file}: {e}")

        print(f"📘 Found {len(chapters)} chapters manually in extracted folder.")
        return chapters


    def get_pending_chapters(self, max_chapters_to_run: int = 0, start_chapter: int = 1, end_chapter: int = 0) -> list:
        """Gets a list of chapters still in 'pending' status, filtered by a range."""
        state = self.load_state()
        pending = []
        count = 0

        chapter_keys = sorted(state['chapters'], key=lambda x: int(x))
        for chapter_key in chapter_keys:
            chapter_index = int(chapter_key)

            if chapter_index < start_chapter:
                continue
            if end_chapter != 0 and chapter_index > end_chapter:
                continue

            data = state['chapters'][chapter_key]
            if data['status'] == 'pending':
                if max_chapters_to_run == 0 or count < max_chapters_to_run:
                    pending.append({'index': chapter_index, **data})
                    count += 1

        return pending

    
    def update_chapter_state(self, chapter_index: int, status: str, rewritten_text: Optional[str] = None, summary: Optional[str] = None, error: Optional[str] = None):
        """Updates the state of a single chapter."""
        state = self.load_state()
        state = self.load_state()
        chapter_key = str(chapter_index)
        if chapter_key in state['chapters']:
            state['chapters'][chapter_key]['status'] = status
            if rewritten_text:
                rewritten_path = os.path.join(self.rewritten_txt_dir, state['chapters'][chapter_key]['rewritten_text_file'])
                with open(rewritten_path, 'w', encoding='utf-8') as f:
                    f.write(rewritten_text)
            if summary:
                state['chapters'][chapter_key]['summary'] = summary
            if error:
                state['chapters'][chapter_key]['error'] = error
            self.save_state(state)
            
    def display_status(self):
        """Prints a summary of the project's status."""
        state = self.load_state()
        if not state:
            print("Project state not found or empty.")
            return

        total = state.get('totalChapters', 0)
        chapters = state.get('chapters', {})
        
        status_counts = {'pending': 0, 'completed': 0, 'failed': 0}
        for data in chapters.values():
            status_counts[data['status']] += 1

        print(f"\n--- Project Status: {self.project_name} ---")
        print(f"Total Chapters: {total}")
        print(f"  - Completed: {status_counts['completed']}")
        print(f"  - Pending:   {status_counts['pending']}")
        print(f"  - Failed:    {status_counts['failed']}")
        
        if status_counts['failed'] > 0:
            print("\nFailed Chapters:")
            for num, data in chapters.items():
                if data['status'] == 'failed':
                    print(f"  - Chapter {num}: {data['error']}")
        print("--------------------------------------\n")

    def package_final_epub(self):
      """Injects rewritten text into a copy of the source EPUB."""
      temp_dir = os.path.join(self.project_dir, "temp_package")
      if os.path.exists(temp_dir):
          shutil.rmtree(temp_dir)
  
      # Create fresh copy of extracted source
      shutil.copytree(self.extracted_dir, temp_dir)
  
      state = self.load_state()
  
      # Locate OPF file
      opf_path = None
      for root, _, files in os.walk(temp_dir):
          for file in files:
              if file.endswith(".opf"):
                  opf_path = os.path.join(root, file)
                  break
          if opf_path:
              break
  
      if not opf_path:
          raise FileNotFoundError("Could not locate OPF file in temp_package.")
  
      # Parse OPF for ID → href mapping
      id_to_href = {}
      with open(opf_path, 'r', encoding='utf-8') as f:
          soup = BeautifulSoup(f.read(), 'xml')
          for item in soup.find_all('item'):
              item_id = item.get('id') # type: ignore
              href = item.get('href') # type: ignore
              if item_id and href:
                  id_to_href[item_id] = href
  
      print("Injecting rewritten chapters into EPUB structure...")
      for chapter_num_str, data in tqdm(state['chapters'].items(), desc="Updating XHTML"):
          if data['status'] != 'completed':
              continue
  
          # Some EPUBs use id = 'content/Chapter1.xhtml', so strip path and extension
          full_id = data['id'].replace('\\', '/').split('/')[-1].split('.')[0]  # e.g. 'Chapter1'
          # Try to find href whose basename matches the id
          matched_href = None
          for href in id_to_href.values():
              if os.path.splitext(os.path.basename(href))[0] == full_id:
                  matched_href = href
                  break
  
          if not matched_href:
              print(f"⚠️ No href found in OPF for ID {data['id']}")
              continue
  
          item_path = os.path.join(os.path.dirname(opf_path), matched_href)
          if not os.path.exists(item_path):
              print(f"⚠️ XHTML file not found for chapter {chapter_num_str} at {item_path}")
              continue
  
          # Read rewritten text file (e.g. chapter_001.txt)
          rewritten_txt_path = os.path.join(self.rewritten_txt_dir, data['rewritten_text_file'])
          if not os.path.exists(rewritten_txt_path):
              print(f"⚠️ Missing rewritten text file: {rewritten_txt_path}")
              continue
  
          with open(rewritten_txt_path, 'r', encoding='utf-8') as f:
              rewritten_content = f.read()
  
          xhtml_body = self._text_to_xhtml_body(rewritten_content)
  
          with open(item_path, "r+", encoding="utf-8") as f:
              soup = BeautifulSoup(f.read(), "lxml")
              body_tag = soup.find("body")
              if body_tag:
                  body_tag.clear() # type: ignore
                  new_body_soup = BeautifulSoup(f"<body>{xhtml_body}</body>", "lxml")
                  if new_body_soup.body:
                      for child in new_body_soup.body.contents:
                          body_tag.append(child) # type: ignore
              f.seek(0)
              f.write(str(soup))
              f.truncate()
  
      # Repackage EPUB
      final_epub_path = self.get_final_epub_path()
      with zipfile.ZipFile(final_epub_path, 'w', zipfile.ZIP_DEFLATED) as zf:
          mimetype_path = os.path.join(temp_dir, 'mimetype')
          if os.path.exists(mimetype_path):
              zf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
  
          for root, _, files in os.walk(temp_dir):
              for file in files:
                  if os.path.basename(file) == 'mimetype':
                      continue
                  full_path = os.path.join(root, file)
                  arcname = os.path.relpath(full_path, temp_dir)
                  zf.write(full_path, arcname)
  
      shutil.rmtree(temp_dir)
      print(f"✅ Final EPUB created at: {final_epub_path}")


    
    def get_final_epub_path(self) -> str:
        config = self.load_config()
        base_name = os.path.splitext(config['sourceEpub'])[0]
        # Use a global default for suffix if needed
        suffix = ConfigManager().get_default('output_suffix') or "_rewritten"
        return os.path.join(self.final_epub_dir, f"{base_name}{suffix}.epub")

    def _text_to_xhtml_body(self, text: str) -> str:
        """Converts multi-line text with simple markdown to an XHTML body string."""
        # A simplified version of your original txt_to_xhtml logic
        def smart_punctuation(line):
            return line.replace('...', '…').replace('--', '—')

        def parse_inline_markup(line):
            line = (line.replace("&", "&").replace("<", "<").replace(">", ">"))
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', line)
            return smart_punctuation(line)

        html_lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\s*(\*\*\*|---)\s*$', line):
                html_lines.append("<hr/>")
            elif line.startswith('#'):
                hashes = re.match(r'(#+)', line).group(1) # type: ignore
                level = len(hashes)
                content = parse_inline_markup(line[level+1:].strip())
                html_lines.append(f"<h{level}>{content}</h{level}>")
            else:
                html_lines.append(f"<p>{parse_inline_markup(line)}</p>")
        return "\n".join(html_lines)