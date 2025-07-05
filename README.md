# 🪄 AI\_epub\_edits

> ✍️ *Rewrite EPUB chapters into a vivid, cinematic style using your favorite AI model — with a modular, project-based architecture for full automation, concurrency, and content fidelity.*

-----

## 📚 **Overview**

**AI\_epub\_edits** is a powerful and modular toolchain for transforming chapters in EPUB files into beautifully rewritten prose using generative AI. It gives you precise control over structure, style, and formatting, all managed through a clean command-line interface.

This tool is designed for writers, editors, and translators who want to elevate their prose, ensuring that the original plot, dialogue, and terminology are perfectly preserved while infusing the text with a new, professionally crafted style.

**Core Components:**

  - **`main.py`**: The central entry point for creating, running, and managing all rewrite projects.
  - **`core/`**: A directory containing the engine of the application:
      - **`project_manager.py`**: Handles the entire lifecycle of a project, from creation and file organization to packaging the final EPUB.
      - **`orchestrator.py`**: Coordinates the rewriting pipeline, managing the AI provider, building prompts, and processing chapters.
      - **`config_manager.py`**: Manages global and project-level configurations, including API keys and rate limits.
      - **`context_manager.py`**: Intelligently creates and manages contextual information, such as glossaries and chapter summaries, to ensure continuity.
  - **`ai_providers/`**: A modular directory that allows you to plug in different AI services. It currently supports Google Gemini, OpenAI, and Google AI Studio.

**✨ Before & After Showcase**
Here’s a quick comparison showing the transformation from the original text to the cinematic, rewritten version.

| Original Prose | Cinematic Rewrite |
| :---: | :---: |
| ![Before Screenshot](assets/before.jpg) | ![After Screenshot](assets/after.jpg) |


-----

## 🎯 **Key Features**

  - ✅ **Project-Based Workflow**: Organize your rewrites into distinct projects, each with its own source files, configuration, and output.
  - ✅ **Multi-Provider Support**: Seamlessly switch between different AI providers (`Gemini`, `OpenAI`, `AIStudio`) and models to find the perfect fit for your project.
  - ✅ **Style-Preserving Rewrites**: Use a style reference text to guide the AI, ensuring the output matches your desired tone and prose style.
  - ✅ **Concurrent Processing & Rate-Limiting**: Optimized for performance with asynchronous operations and intelligent rate-limiting to respect API limits.
  - ✅ **Context-Aware AI**: A `ContextManager` generates a project-specific glossary and uses rolling chapter summaries to maintain consistency in terminology and plot.
  - ✅ **Robust EPUB Parsing & Injection**: Reliably extracts chapters from EPUBs and injects the rewritten content back in, preserving metadata and structure.
  - ✅ **Command-Line Interface**: A clean, easy-to-use CLI for managing the entire workflow, from project creation to final packaging.

-----

## 🧠 **How It Works**

The workflow is managed by a central **Orchestrator** which coordinates the different modules.

### 1\. **Project Creation** (`main.py new`)

  - You create a new project with a name, a source EPUB, and a style reference text.
  - The **ProjectManager** sets up a dedicated directory structure for the project, unzips the source EPUB, and initializes a state file to track progress.

### 2\. **Running the Pipeline** (`main.py run`)

  - The **Orchestrator** takes over, loading the project configuration and selecting the specified AI provider.
  - For each chapter, it uses the **ContextManager** to build a detailed prompt that includes:
      - The style reference text.
      - A glossary of key terms to ensure consistency.
      - A summary of the previous chapter for continuity.
  - The prompt is sent to the selected AI provider, which rewrites the chapter.
  - The rewritten text and a new summary are saved, and the project state is updated.

### 3\. **Packaging the Final EPUB** (`main.py package`)

  - Once chapters are rewritten, the **ProjectManager** injects the new, professionally formatted XHTML content back into a copy of the original EPUB structure.
  - It then re-zips the files into a new, final EPUB, ready for you to read.

-----

## 🚀 **Getting Started**

### 🔗 **Requirements**

First, install the necessary dependencies:

```bash
pip install -r requirements.txt
```

### 🔑 **Setup**

1.  **Get API Keys**: Obtain an API key from your desired AI provider (e.g., Google AI Studio, OpenAI).
2.  **Configure the Tool**: Open `config.ini` and paste your API key(s) into the `[API_KEYS]` section. You can also set your default provider and model here.
    ```ini
    [API_KEYS]
    GOOGLE_API_KEY = PASTE_YOUR_GEMINI_API_KEY_HERE
    AISTUDIO_API_KEY = PASTE_YOUR_AI_STUDIO_API_KEY_HERE
    OPENAI_API_KEY = PASTE_YOUR_OPENAI_API_KEY_HERE
    ```
3.  **Prepare a Style Reference**: Create a `.txt` file that contains a sample of the writing style you want the AI to emulate. A chapter from a professionally published novel in a similar genre works best.

### ⚙️ **Usage**

The tool is operated through `main.py`.

**1. Create a New Project:**
Use the `new` command to initialize your project.

```bash
python main.py new --name "MyBookProject" --epub "/path/to/your/book.epub" --style_ref "/path/to/style.txt"
```

**2. Run the Rewriting Pipeline:**
Use the `run` command to start the AI-powered rewriting process.

```bash
python main.py run --name "MyBookProject"
```

You can also **override** the default settings from `config.ini` using command-line arguments:

```bash
python main.py run --name "MyBookProject" --provider openai --model gpt-4o --start 5 --end 10
```

**3. Package the Final EPUB:**
After the pipeline has finished, use the `package` command to generate the final, rewritten EPUB file.

```bash
python main.py package --name "MyBookProject"
```

**4. Check Project Status:**
At any time, you can check the progress of your project with the `status` command.

```bash
python main.py status --name "MyBookProject"
```

-----

## 📁 **Output**

All files for a project are neatly organized within the `projects/` directory under your project's name:

  - **`0_source/`**: Contains the original EPUB you provided.
  - **`1_extracted/`**: The unzipped content of the source EPUB.
  - **`2_rewritten_txt/`**: The rewritten chapters, saved as individual `.txt` files.
  - **`3_final_epub/`**: Your completed, rewritten EPUB will be saved here.
  - **`project_config.json`**: The specific configuration for this project.
  - **`project_state.json`**: Tracks the status of each chapter (pending, completed, or failed).
  - **`rewriter.log`**: A log file for debugging and tracking the rewriting process.

-----

## ⚠️ **Notes & Limitations**

  - The tool is designed to be robust but works best with cleanly formatted EPUB files. It includes fallbacks for various parsing issues.
  - API rate limits, especially on free tiers, can affect processing speed. The tool has built-in rate-limiting and retry logic to handle this gracefully.
  - The quality of the rewrite is highly dependent on the quality of your **style reference** and the **prompt template**. Experiment with different styles and prompts in the `prompt_templates/` directory to get the best results.

-----

## 💡 **Future Ideas**

  - GUI wrapper for easy project management.
  - Real-time preview of rewritten chapters in a browser.
  - Support for additional input formats (`.txt`, `.docx`).
  - A style-tuning dashboard to dynamically adjust prompts.

-----

## 🧙‍♂️ **Contribute**

Pull requests are welcome\! Feel free to fork the project and submit improvements or new features.

> *Crafted with love by a writer who believes every story deserves a great editor.* 💜
> (Also with distaste for extremely shitty grammar 😑)