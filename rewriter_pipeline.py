# rewriter_pipeline.py
"""
EPUB to TXT Chapter Rewriter - Public Version

This script rewrites chapters from an LNReader exported EPUB using Google Gemini API to enhance prose 
into a more cinematic, sensory, and immersive style based on a provided reference.

USAGE:
 1. Install dependencies:
    pip install ebooklib beautifulsoup4 google-generativeai tqdm

 2. Get your Google AI Studio API key:
    - https://aistudio.google.com/apikey
    - Do NOT connect your billing account (unless you know what you're doing); this is a free API key for your private use.
    - Rate limits apply for the free tier - https://ai.google.dev/gemini-api/docs/rate-limits
    - My default settings are Gemini 2.0 Flash which has a 200 Requests = Chapters per Day limit.

 3. Provide the required inputs below:
    - EPUB_FILE_PATH: Path to the source .epub file (this is the LNReader export)
    - STYLE_REFERENCE_TEXT: A passage that defines your preferred writing style (eg. a 2000 word chapter from a book)
    - AI_STUDIO_API_KEY: Your Google AI Studio API key

 4. Run the script:
    python rewriter_pipeline.py

 5. Output will be saved in the 'rewritten_novel/' directory.

NOTE: Secrets and private file paths must be added by the user. group[1], .configure and .GenerativeModel red errors are expected if typechecks are on.
Just ignore them, they are not relevant to the script's functionality.
"""

import os
import re
import json
import time
import logging
import asyncio
from typing import List, Dict, Optional

# --- Third-party Libraries ---
# pip install ebooklib beautifulsoup4 google-generativeai tqdm
from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm as async_tqdm
from tqdm import tqdm
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted
# ======================================================================
# USER-PROVIDED INPUTS (REQUIRED)
# ======================================================================
EPUB_FILE_PATH = ""  # <- Provide path to your source EPUB file eg. in the same directory as this script, {title}.epub
STYLE_REFERENCE_TEXT = """ """  # <- Paste your preferred writing style sample here eg. a singular 2000 word chapter from a book or a passage that defines your style
AI_STUDIO_API_KEY = ""  # <- Replace with your API key

# ================================================================================
# OPTIONAL CONFIGURATION 
# (CAN BE LEFT AS DEFAULT, IF CHANGED DO THE SAME IN THE TXT TO XHTML CONVERTER)
# ================================================================================
OUTPUT_DIR = "rewritten_novel"
LOG_FILE = "rewriter.log"
PROMPT_LOG_FILE = "prompt_log.txt"
MODEL_NAME = "gemini-2.0-flash"
# API Rate Limits (adjust as needed)
# These are the default limits for Gemini 2.0 Flash, a bit rounded down for safety
RPM_LIMIT = 13
TPM_LIMIT = 800000
MAX_CONCURRENT_CALLS = 1
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 20.0

# ==============================================================================
# RATE LIMITER
# ==============================================================================
class RateLimiter:
    """Manages API call rates for both TPM and RPM with a unified delay mechanism."""
    def __init__(self, tpm_limit: int, rpm_limit: int):
        self.tpm_capacity = float(tpm_limit)
        self.tokens = float(tpm_limit)
        self.refill_rate_per_second = float(tpm_limit) / 60.0
        self.last_refill_time = time.monotonic()
        self._rpm_delay = 60.0 / rpm_limit if rpm_limit > 0 else 0
        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        self.tokens = min(self.tpm_capacity, self.tokens + elapsed * self.refill_rate_per_second)
        self.last_refill_time = now

    async def wait_for_tokens(self, tokens_to_consume: int):
        async with self._lock:
            self._refill()
            if tokens_to_consume > self.tpm_capacity:
                logging.warning(f"Request for {tokens_to_consume} tokens exceeds bucket capacity of {self.tpm_capacity}.")

            wait_time = 0
            if tokens_to_consume > self.tokens:
                required_tokens = tokens_to_consume - self.tokens
                wait_time = required_tokens / self.refill_rate_per_second
            
            if wait_time > 0:
                logging.info(f"TPM Limit: Pausing for {wait_time:.2f}s to generate {tokens_to_consume} tokens.")
                await asyncio.sleep(wait_time)
                self._refill()
            
            self.tokens -= tokens_to_consume

    async def enforce_rpm_delay(self):
        if self._rpm_delay > 0:
            await asyncio.sleep(self._rpm_delay)

# ==============================================================================
# EPUB PROCESSING
# ==============================================================================
class EbookProcessor:
    """Extracts, cleans, and structures chapters from an EPUB file."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.chapters: List[Dict[str, str]] = []

    def _html_to_text(self, html_content: str) -> str:
        """Converts raw chapter HTML to clean, readable text."""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        # Get text, preserving some structure with separators
        text = soup.get_text(separator='\n', strip=True)
        # Consolidate multiple newlines into a maximum of two
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def process(self):
        """Custom processing for this specific EPUB structure from LNReader"""
        logging.info(f"Processing EPUB file: {self.file_path}")
        if not os.path.exists(self.file_path):
            logging.error(f"EPUB file not found at: {self.file_path}")
            return

        try:
            cleaned_path = self.file_path.replace(".epub", "_cleaned.epub")
            clean_epub_metadata(self.file_path, cleaned_path)
            
            # Force ignore missing cover
            book = epub.read_epub(cleaned_path, options={
                'ignore_ncx': True,
                'ignore_missing_files': True
            })


            # Dynamically detect all chapter files matching the pattern "content/ChapterX.xhtml"
            chapter_files = []
            for item in book.get_items():
                name = item.get_name()
                if re.match(r"content/Chapter\d+\.xhtml$", name):
                    chapter_files.append(name)

            for item in book.get_items():
                if item.get_name() in chapter_files:
                    try:
                        html_content = item.get_content().decode('utf-8', 'ignore')
                        text_content = self._html_to_text(html_content)
                        
                        # Extract title from filename if needed
                        chapter_num = int(re.search(r'Chapter(\d+)', item.get_name()).group(1))
                        title = f"Chapter {chapter_num}"
                        
                        self.chapters.append({
                            "title": title,
                            "original_text": text_content,
                            "id": item.get_name()
                        })
                    except Exception as e:
                        logging.warning(f"Error processing {item.get_name()}: {e}")
                        continue

            logging.info(f"Extracted {len(self.chapters)} chapters from the EPUB.")
        except Exception as e:
            logging.error(f"Failed to process EPUB: {e}", exc_info=True)


def clean_epub_metadata(epub_path: str, cleaned_epub_path: str) -> str:
    """
    Unzips the EPUB, removes broken cover references from the OPF file, and re-zips it.
    Returns the path to the cleaned EPUB.
    """
    import zipfile
    import tempfile
    import shutil

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

        # Read, clean, and write back the OPF
        with open(opf_path, 'r', encoding='utf-8') as f:
            opf_content = f.read()

        # Remove <meta name="cover" content="..."/> and <item ... properties="cover-image" />
        opf_content = re.sub(r'<meta\s+name="cover"\s+content=".*?"\s*/?>', '', opf_content)
        opf_content = re.sub(r'<item\s+[^>]*properties="cover-image"[^>]*/?>', '', opf_content)

        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(opf_content)

        # Create the cleaned EPUB
        with zipfile.ZipFile(cleaned_epub_path, 'w') as zip_write:
            for foldername, subfolders, filenames in os.walk(tmpdir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, tmpdir)
                    compress_type = zipfile.ZIP_STORED if arcname == 'mimetype' else zipfile.ZIP_DEFLATED
                    zip_write.write(file_path, arcname, compress_type=compress_type)

    return cleaned_epub_path
            
# ==============================================================================
# REWRITING ORCHESTRATOR
# ==============================================================================
class RewriterPipeline:
    """Orchestrates the entire novel rewriting process."""
    def __init__(self):
        self._setup_logging()
        genai.configure(api_key=AI_STUDIO_API_KEY)
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.rate_limiter = RateLimiter(tpm_limit=TPM_LIMIT, rpm_limit=RPM_LIMIT)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)
        self.api_call_lock = asyncio.Lock() # Serializes the final API call

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(LOG_FILE, 'w'), logging.StreamHandler()])

    def _build_prompt(self, chapter_text: str) -> str:
        # This prompt is carefully engineered based on your request.
        return f"""
You are a master literary editor with a talent for transforming dry, amateur, shitty prose into a cinematic, immersive, and sensory experience.
Your task is to rewrite the provided book chapter to match the style of the 'Style Reference' below. Infer some context for additional details, but do not add any new content or change the plot.

**VERY CRITICAL RULES:**
1.  **DO NOT CHANGE THE PLOT.** The sequence of events, character actions, and outcomes must remain identical.
2.  **DO NOT CHANGE CHARACTER OR PLACE NAMES.** 'Alex' must remain 'Alex'.
3.  **DO NOT CHANGE DIALOGUE CONTENT.** The exact words characters speak must be preserved, in a better and more professional format.
4.  **DO NOT CHANGE IN-UNIVERSE SYSTEMS OR LORE.** Concepts like "Legacy Tombs", "Titans", or game mechanics must not be altered.

**YOUR GOAL (THE STYLE TRANSFORMATION):**
-   **Show, Don't Tell:** Instead of saying "He looked happy and visibly nervous," describe the "unsteady grin fighting a tremor in his hand" or "a bead of sweat tracing a path down his temple."
-   **Engage the Senses:** The reference is rich with sounds (hum, patter, shrieks), smells (stale coffee, ozone, blood), and feelings (cold stone, damp wool, electrical energy). Infuse the new chapter with sensory details.
-   **Elevate Vocabulary & Pacing:** Use stronger verbs, more evocative adjectives, and vary sentence structure. Contrast long, descriptive sentences with short, punchy ones for impact.
-   **Internal Monologue:** Expand on the character's internal thoughts and feelings, as seen with Kaelan's internal monologue. Do NOT make stuff up, but enhance the existing thoughts to be more vivid and introspective.
-   **Cinematic Descriptions:** Describe settings and actions as if directing a movie scene.
**DO NOT ADD ANYTHING OUT OF CONTEXT.** Only rewrite the existing text to match the style of the reference with some additional sensory details.

---
**STYLE REFERENCE (Emulate this tone and technique):**
{STYLE_REFERENCE_TEXT}
---

**CHAPTER TO REWRITE (Apply the style to this text):**
{chapter_text}
---

**REWRITTEN CHAPTER (Output only the rewritten text):**
"""

    async def _rewrite_chapter_task(self, chapter_data: Dict[str, str], index: int) -> Optional[Dict[str, str]]:
        """A single, robust task to rewrite one chapter."""
        async with self.semaphore:
            prompt = self._build_prompt(chapter_data["original_text"])
            
            try:
                # Token counting is a lightweight check
                token_count = await self.model.count_tokens_async(prompt)
                self._log_prompt(index, prompt, token_count.total_tokens)
                await self.rate_limiter.wait_for_tokens(token_count.total_tokens)
            except Exception as e:
                logging.error(f"Chapter {index+1}: Token counting failed: {e}")
                return None

            async with self.api_call_lock:
                for attempt in range(API_RETRY_ATTEMPTS + 1):
                    try:
                        logging.info(f"Submitting Chapter {index+1} for rewrite (Attempt {attempt+1})...")
                        response = await self.model.generate_content_async(
                            prompt,
                            generation_config=GenerationConfig(temperature=0.7)
                        )
                        await self.rate_limiter.enforce_rpm_delay()
                        
                        chapter_data["rewritten_text"] = response.text
                        logging.info(f"Successfully rewrote Chapter {index+1}.")
                        return chapter_data

                    except ResourceExhausted as e:
                        wait_time = API_RETRY_DELAY * (2 ** attempt)
                        logging.warning(f"Chapter {index+1}: ResourceExhausted. Pausing for {wait_time:.1f}s.")
                        await asyncio.sleep(wait_time)
                    except Exception as e:
                        logging.error(f"Chapter {index+1}: An unexpected API error occurred on attempt {attempt+1}: {e}", exc_info=True)
                        await asyncio.sleep(API_RETRY_DELAY)
            
            logging.error(f"Chapter {index+1}: All rewrite attempts failed.")
            return None

    def _save_chapter(self, chapter_data: Dict[str, str], chapter_num: int):
        """Saves a single rewritten chapter to a file using a structured naming format."""
        # Extract clean chapter number from the ID (e.g., content/Chapter3.xhtml -> Chapter3 -> 3)
        match = re.search(r'Chapter(\d+)', chapter_data['id'])
        chapter_index = int(match.group(1)) if match else chapter_num

        # Ensure output filenames are ordered and human-readable (starting from 1)
        filename = f"chapter_{chapter_index:03d}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Fully clean the directory before writing
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        else:
            # Clear previous chapter files
            for file in os.listdir(OUTPUT_DIR):
                if file.startswith("chapter_") and file.endswith(".txt"):
                    os.remove(os.path.join(OUTPUT_DIR, file))

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Rewritten: {chapter_data['title']}\n\n")
                f.write(chapter_data.get("rewritten_text", "ERROR: REWRITING FAILED FOR THIS CHAPTER"))
        except IOError as e:
            logging.error(f"Failed to write file {filepath}: {e}")

    def _log_prompt(self, chapter_index: int, prompt: str, token_count: int):
        """Logs the full prompt text and its token count to a log file."""
        header = f"\n{'='*80}\nCHAPTER {chapter_index + 1} PROMPT | Token Count: {token_count}\n{'='*80}\n"
        try:
            with open(PROMPT_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(header)
                f.write(prompt)
                f.write("\n\n")
        except Exception as e:
            logging.warning(f"Failed to log prompt for Chapter {chapter_index + 1}: {e}")

    async def run(self):
        """Main execution flow of the pipeline."""
        logging.info("--- Starting Novel Rewriter Pipeline ---")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
                # Clear previous prompt log
        if os.path.exists(PROMPT_LOG_FILE):
            os.remove(PROMPT_LOG_FILE)
        processor = EbookProcessor(EPUB_FILE_PATH)
        processor.process()

        if not processor.chapters:
            logging.error("No chapters found to process. Exiting.")
            return
            
        tasks = [self._rewrite_chapter_task(chapter, i) for i, chapter in enumerate(processor.chapters)]
        
        rewritten_chapters = []
        with tqdm(total=len(tasks), desc="Rewriting Chapters") as pbar:
            for future in asyncio.as_completed(tasks):
                result = await future
                if result:
                    rewritten_chapters.append(result)
                pbar.update(1)
        
        logging.info("All rewriting tasks complete. Now saving files...")
        
        # Sort chapters by their original order before saving
        def extract_chapter_number(chapter):
            match = re.search(r'(\d+)', chapter['title'])
            return int(match.group(1)) if match else 0
        rewritten_chapters.sort(key=extract_chapter_number)
        
        for i, chapter_data in enumerate(rewritten_chapters):
            self._save_chapter(chapter_data, i + 1)

        cleaned_path = EPUB_FILE_PATH.replace(".epub", "_cleaned.epub")
        if os.path.exists(cleaned_path):
            os.remove(cleaned_path)
            logging.info(f"Removed temporary file: {cleaned_path}")

        logging.info(f"Pipeline finished. Check the '{OUTPUT_DIR}' folder.")


if __name__ == "__main__":
    if AI_STUDIO_API_KEY == "YOUR_AI_STUDIO_API_KEY_HERE":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR: Please replace 'YOUR_AI_STUDIO_API_KEY_HERE' !!!")
        print("!!! in the script with your actual Google AI Studio key.!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        exit(1)
    else:
        pipeline = RewriterPipeline()
        asyncio.run(pipeline.run())