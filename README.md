# Side-by-Side Dual-Language Reading & Learning Web App

An interactive dual-pane ebook / text reader designed for language learning. Features synchronized sentence highlighting, word and phrase alignment matching, verb root/tense analysis, keyboard shortcuts, and customizable reading themes.

---

## Features

- 📖 **Dual-Pane Synchronized Ebook Reader**: Side-by-side view with original text on the left and English translation on the right.
- 🌐 **Automatic Non-English Language Detection**: Identifies the primary source language in each section (Spanish, Italian, French, German, etc.) and displays it in the bottom status bar.
- 🎯 **Synchronized Sentence Hover**: Hover over a sentence in either pane to highlight its counterpart in real-time across panes in the other language.
- 🔤 **Dual-Tone Word Sub-Matching**:
  - **Darker Orange**: Highlights exact target word sub-matches.
  - **Lighter Orange**: Highlights parent phrase context.
- 💡 **Verb Grammar & Infinitive Popovers**: Click conjugated verbs in the source language to view infinitive root verbs and tense/person details.
- 📜 **EPUB Structure & CSS Support**: Renders chapter HTML formatting (headings, paragraphs, blockquotes) directly from EPUB files.
- 🎨 **Reading Themes & Font Scaling**: Built-in Light, Dark, and Sepia themes with dynamic font scaling controls (`A-` / `A+`).
- ⚡ **Local Alignment Caching**: Caches Gemini API translations locally in `./cache` for instant reloading.
- ⌨️ **Keyboard Navigation**: `ArrowLeft` and `ArrowRight` shortcut keys for section navigation.

---

## Requirements & Environment Setup

### 1. Prerequisites
- **Python**: Version 3.10+ (managed via [`uv`](https://github.com/astral-sh/uv))
- **Gemini API Key**: Set your key in `.env` or as an environment variable to enable Gemini translation and alignment.

### 2. Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Installation & Setup

1. **Clone or Navigate to the Workspace**:
   ```bash
   git clone git@github.com:SumitBando/SideBySideReader.git
   cd SideBySideReader
   ```

2. **Install Dependencies using `uv`**:
   ```bash
   uv sync
   ```

---

## Usage Instructions

### 1. Launch the Application
Start the (FastHTML web server) application:
```bash
uv run python main.py
```
The app will serve locally at **http://localhost:5001/**.

### 2. Ebook & Section Navigation
- Use the **Book Select Dropdown** to choose any available EPUB file in the root folder.
- Use the **Chapter Select Dropdown** (populated with actual chapter/story titles) or click **Previous Section** / **Next Section** buttons to turn pages.
- Alternatively, use keyboard shortcuts:
  - `ArrowLeft`: Navigate to Previous Section.
  - `ArrowRight`: Navigate to Next Section.

### 3. Reader Controls & Interactivity
- **Status Bar Language**: View the detected source language (e.g. `Language: Italian` or `Language: Spanish`) in the bottom bar.
- **Sentence Hover**: Hover over sentences to visually link source and translation.
- **Word Selection**: Click individual words to see exact word sub-matches and phrase alignments.
- **Verb Analysis**: Click source language verbs to display popovers with root infinitive and tense info.
- **Theme Controls**: Click **Light**, **Dark**, or **Sepia** to change theme mode.
- **Font Sizing**: Click **A-** or **A+** to decrease/increase font size.

---

## Verification & Testing

To run the automated client smoke test suite and verify Section 1 alignment integrity:
```bash
uv run python tests/client.py
```
