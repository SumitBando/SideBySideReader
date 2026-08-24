# Specifications: Side-by-Side Dual-Language Reader

## 1. Application Overview
The **Side-by-Side Dual-Language Reader** is an interactive web application designed for language learners. It renders EPUB ebooks in a dual-pane layout with synchronized sentence highlighting, word/phrase alignment matching, and verb grammar analysis.

---

## 2. Core Architecture & Tech Stack
* **Language & Runtime**: Python 3.14+ managed via `uv`
* **Web Framework**: **FastHTML** (`python-fasthtml`) with `uvicorn`
* **EPUB Parsing**: `ebooklib` + `BeautifulSoup4`
* **Translation & Alignment Engine**: Gemini API (`google-genai`) with fallback online translator
* **Local Caching**: File-based JSON caching in `./cache` (MD5 hash keyed per sentence block)
* **Frontend Interactivity**: Vanilla JS & CSS Grid/Flex design system with theme tokens

---

## 3. Detailed Features & Behaviors

### 3.1 Dual-Pane Layout & Typography
* **Left Pane**: Original source text displaying detected language name in header (e.g. `Original Text (Spanish)`, `Original Text (Italian)`).
* **Right Pane**: Translated target text (`English Translation`).
* **Vertical Scrollbars**: Both panes feature dedicated, visible vertical scrollbars (`overflow-y: scroll`) with theme-adaptive styling.
* **DOM Tag Preservation**: HTML heading structures (`<h1>`-`<h6>`), paragraphs (`<p>`), blockquotes, and `<div>` tags from original EPUB files are preserved in both panes.
* **Theme Modes**:
  * Light Mode (default): slate/white palette
  * Dark Mode: deep slate `#0f172a`
  * Sepia Mode: warm reading tones `#fbf0d9`
* **Font Scaling**: Dynamic font sizing (`A-` / `A+` controls) stored in browser `localStorage`.

### 3.2 EPUB Extraction & Structure Preservation
* Extracts documents and embedded CSS from `.epub` files in the root project directory.
* **Complete Chapter Extraction**: Extracts all sentences and blocks across the entire chapter without arbitrary sentence truncation.
* **Chapter Title Resolution**: Dynamically extracts actual chapter/section names from EPUB Table of Contents (TOC), HTML heading tags (`<h1>`-`<h6>`), and document structure patterns, falling back to `Section N` only when no title is defined.
* Filters out nested container elements to prevent duplicate text extraction.
* Sentence Segmentation: Splitting based on language punctuation rules (`.!?¿¡`).

### 3.3 Dynamic Language Identification, Translation & Alignment Engine
* **Chunked Batch Processing**: Handles full chapter content of any length by chunking sentences into batches of up to 25 sentences for Gemini API alignment, caching each batch individually for fast reloading.
* **Automatic Language Identification**: Dynamically detects the primary non-English language in each section (e.g. Spanish, Italian, French, German, Russian, etc.) or identifies `English` if the section is entirely in English.
* **Status Bar Language & Chapter Display**: Bottom status bar renders the detected language (e.g. `Language: Italian`) alongside the active chapter name, index, and token counts.
* **Translation to English**: Translates non-English source language text into English while preserving English blocks/headings as-is without reverse translation.
* **Dual Alignment Output**:
  * Sentence translation mapping (`src` $\leftrightarrow$ `tgt`).
  * Word and phrase alignments (`src_words` $\leftrightarrow$ `tgt_words`).
  * Verb Grammatical Analysis: Returns `is_verb`, `infinitive` (root verb), and `tense_person` metadata for conjugated verbs in the detected source language.

### 3.4 Interactive Dual Highlighting & Navigation
* **Synchronized Sentence Hover**:
  * Hovering over a sentence in either pane instantly highlights the corresponding sentence in the opposing pane (`.sentence.active`).
* **Word/Phrase Selection on Click**:
  * **Darker Orange** (`.active-word-exact`): Highlights exact target word sub-matches.
  * **Lighter Orange** (`.active-word-phrase`): Highlights parent multi-word phrase alignments.
* **Verb Root & Grammar Popover**:
  * Clicking a conjugated verb token in the source pane opens a popover displaying its infinitive root and tense/person breakdown.
  * Auto-Dismiss: The popover automatically closes when moving the mouse to a different sentence or leaving sentence bounds.
* **Opposing Pane Auto-Scroll**:
  * Clicking/selecting a sentence smoothly scrolls the corresponding sentence in the opposite pane into view (`scrollIntoView`).
* **Section & Book Navigation**:
  * **Chapter Select Dropdown**: Populated with resolved chapter and section names for easy switching.
  * Keyboard Shortcuts: `ArrowLeft` (Previous Section) and `ArrowRight` (Next Section).
  * Boundary Guards: Disable Previous/Next buttons at book boundaries (`chapter_idx <= 0` / `chapter_idx >= total - 1`).
  * Visual Loading Feedback: Full-screen blurred overlay with CSS spinner during uncached API translation requests.

---

## 4. Test Suite & Verification
* Automated Verification Script: `tests/client.py`
* Tests:
  1. FastHTML server status check (HTTP 200 OK).
  2. Multi-language detection verification (validates Spanish and Italian books and sections).
  3. Status bar language display assertion (`#status-language`).
  4. DOM structure verification (`.sentence`, `.word-token`, `.pane`).
  5. Cross-pane token mapping integrity (validates `data-exact-target-ids` and `data-phrase-target-ids` across pane boundaries).

# 5. Model choice
## 1. gemini-3.5-flash-lite (Recommended)
Input Price (per 1M tokens) ~$0.075, Output Price (per 1M tokens) ~$0.30
- Superior Structured Output: 3.5 generation models have higher instruction-following precision when
      generating complex JSON structures (e.g. nested src_words, tgt_words, is_verb, infinitive, and tense_person
      arrays simultaneously across various source languages).
 - Lower Latency: Optimized TTFT (Time-To-First-Token), making uncached page flips noticeably faster for the
      reader.
 - Better Idiomatic Translation: Translates complex idioms and literary phrasing across multiple languages (Spanish, Italian, etc.) naturally while maintaining strict phrase boundaries.