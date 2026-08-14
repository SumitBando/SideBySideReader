# Project Overview: Side-by-Side Dual-Language Reading & Learning Web App

## Goal
Build an interactive, dual-language ebook / text reading web application for language learning.
- **Left Pane**: Original language text (e.g., Spanish, Italian).
- **Right Pane**: Translated English text.
- **EPUB & Text Support**: Extract and paginate side-by-side EPUB content while preserving HTML structure (`<p>`, `<h1>`-`<h6>`, `blockquote`).
- **Interactive Synchronized Highlighting & Alignment**:
  - Hovering a sentence in either language highlights the corresponding sentence in the opposing pane.
  - Clicking a word highlights exact sub-matches (dark orange) and parent phrase context (light orange).
  - Clicking source language verbs opens a popover card showing root infinitive verbs and subject/tense analysis.

## Stack & Tech Architecture
- **Web Framework**: Python **FastHTML** (`python-fasthtml`) running on `uvicorn`.
- **EPUB & Alignment Engine**:
  - `ebooklib` + `BeautifulSoup4` for EPUB extraction.
  - **Gemini API** (`gemini-flash-latest` / `gemini-2.5-flash-lite`) pipeline for batch sentence translation, word/phrase alignment mapping, and verb grammar analysis.
  - Local file caching (`./cache`) for aligned book structures, token indices, and Gemini responses.
- **UI Design & Reader Interactivity**:
  - CSS Grid / Flex dual-pane reader layout.
  - Light, Dark, and Sepia visual theme modes with dynamic font scaling.
  - Client-side JS event handlers for synchronized sentence hover, dual-tone word sub-matching, verb grammar popovers, opposing pane smooth scrolling, and keyboard arrow navigation.

## Current Project Specifications & Docs
- Detailed feature specs: [`specs.md`](file:///home/sumit/sidebyside/specs.md)
- Installation & usage instructions: [`README.md`](file:///home/sumit/sidebyside/README.md)
- Verification test suite: [`tests/client.py`](file:///home/sumit/sidebyside/tests/client.py)

# Documentation
- For feature additions/changes, update specs.md, and check if README.md should be updated. 
- Update GEMINI.md when appropriate

# Source control
Create change lists for review
Do not ask to commit