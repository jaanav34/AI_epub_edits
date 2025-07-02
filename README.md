# 🪄 **AI_epub_edits**

> ✍️ *Rewrite EPUB chapters into a vivid, cinematic style using the FREE tier of Google Gemini — with full automation, concurrency, and content fidelity.*


## 📚 **Overview**

**AI_epub_edits** is a modular toolchain for transforming chapters in EPUB files into beautifully rewritten prose using generative AI, with precise control over structure, style, and formatting. Note that my ebook processor is made specifically for EPUBs exported from the app LNReader and preserves all formatting, structure, and metadata, but is easily modified to other EPUBs.

**Core Components:**
- **`rewriter_pipeline.py`** — Extracts chapters, rewrites them using a prompt-engineered AI model, and logs everything.
- **`txt_to_xhtml.py`** — Converts the rewritten `.txt` chapters back into valid XHTML and injects them into the EPUB structure.

---

## 🎯 **Key Features**

- ✅ **Style-Preserving Rewrites**
- ✅ **Concurrent Processing & Rate-Limiting**
- ✅ **Robust EPUB Parsing & Injection**
- ✅ **Token-Aware Prompt Management**
- ✅ **XHTML-Compliant Output**
- ✅ **Custom Smart Punctuation & Markdown Support**

---

## 🧠 **How It Works**

### 1. `rewriter_pipeline.py`

This script orchestrates the full rewrite pipeline:

- Reads chapters from an EPUB file
- Sends each chapter to a generative AI model (e.g. Gemini)
- Applies **strict rules**:
    - No plot, name, or dialogue changes
    - Style adapted from a provided sample (e.g., a reference chapter)
    - Cinematic and sensory transformation

#### ✨ *Core Classes & Methods*

```python
class RewriterPipeline:
        def __init__():                   # Initializes model, rate limiter, concurrency
        def _build_prompt():              # Constructs style-bound prompt per chapter
        async def _rewrite_chapter_task():# Handles retries, token counting, API calls
        def _save_chapter():              # Saves output as chapter_###.txt
        async def run():                  # Master orchestration method

class RateLimiter:
        def wait_for_tokens():            # Token-per-minute aware limiter
        def enforce_rpm_delay():          # Request-per-minute limiter
```

---

### 2. `txt_to_xhtml.py`

This script injects rewritten `.txt` chapters into the original EPUB directory.

**It:**
- Replaces `<div id="article">` content in each `ChapterX.xhtml` file
- Supports Markdown-style input (headings, bold, italics, HR)
- Preserves EPUB metadata and structure

```python
def replace_chapters(unzipped_dir):  # Parses .txt, converts to XHTML, replaces content
def process_line(line):              # Handles Markdown, HTML escape, smart punctuation
def rezip_epub():                    # Repackages EPUB after injecting new content
```

---

## 🚀 **Getting Started**

### 🔗 Requirements

Install dependencies:

```bash
pip install ebooklib beautifulsoup4 google-generativeai tqdm lxml
```

### 🔑 Setup
0. Almost Mandatory: Prepare your exported EPUB from LNReader.
1. Download the ZIP file of this repository or clone it using git. Put your desired EPUB in the same directory.
2. Get your Google AI Studio API key at https://aistudio.google.com/apikey
    - Do NOT connect your billing account (unless you know what you're doing); this is a free API key for your private use. Never share this with anyone
    - Rate limits apply for the free tier - https://ai.google.dev/gemini-api/docs/rate-limits
    - My default settings are Gemini 2.0 Flash Lite which has a 200 Requests = Chapters per Day limit.
    -This is NOT a product I'm selling, this will be a script running on your own PC with your own, private API key. You can use other models too on Google AI Studio or modify the structure to use ChatGPT API etc. for better rate limits.
3. Paste it into `rewriter_pipeline.py` as `AI_STUDIO_API_KEY`
4. Add your `STYLE_REFERENCE_TEXT` into `rewriter_pipeline.py` (any passage with your intended style, I recommend a chapter from a novel in the same genre)
5. Set the `EPUB_FILE_PATH` (your books's name).epub most likely, to both `rewriter_pipeline.py` and `txt_to_xhtml.py`
6. Set a new name in `txt_to_xhtml.py` to `OUTPUT_EPUB_PATH`

**Run:**
To convert EPUB into rewritten text files:

```bash
python rewriter_pipeline.py
```

Then convert rewritten text files back into EPUB:

```bash
python txt_to_xhtml.py
```

---

## 📁 **Output**

- **Rewritten chapters:** `rewritten_novel/chapter_###.txt`
- **Logs:**  
    - Rewrite: `rewriter.log`  
    - Prompt Debug: `prompt_log.txt`
- **Final EPUB:** Set via `OUTPUT_EPUB_PATH` in `txt_to_xhtml.py`

---

## ⚠️ **Notes & Limitations**

- Only chapters named like `Chapter#.xhtml` are processed. (ie. all LNReader EPUBs will work)
- Designed for EPUBs exported from LNReader, but easily adaptable.
- API limits (free tier): 200 chapters/day, 800K TPM, 12 RPM (Gemini Flash Lite). This is NOT a product I'm selling, this will be a script running on your own PC with your own, private API key. You can use other models too on Google AI Studio or modify the structure to use ChatGPT API etc. for better rate limits.
- Does not hallucinate new content – only stylistic transformation.
- BeautifulSoup/lxml warnings in IDEs can be ignored.

---

## 📌 **License**

This repository is open-source and MIT licensed.
---

<div align="center">


![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

</div>

---

## 💡 **Future Ideas**
- Re-MTL a mistranslated novel into various languages while keeping terminology the same across chapters
- Use a number range eg. [x,y] to rewrite specific chapters only
- Context updates from previous chapters to use in new chapters
- GUI wrapper for EPUB upload/download
- Style tuning dashboard
- Real-time preview in browser
- Support for additional input formats (`.txt`, `.docx`)

---

## 🧙‍♂️ **Contribute**

Pull requests welcome! Feel free to fork the project and submit improvements or new features.

> *Crafted with love by a writer who believes every webnovel deserves a second draft.* 💜
> (Also with distaste for extremely shitty grammar 😑)

