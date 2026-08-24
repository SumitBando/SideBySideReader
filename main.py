import os
import json
import re
from fasthtml.common import *
from epub_parser import extract_chapters_from_epub, split_into_sentences
from aligner import AlignmentEngine

app, rt = fast_app(
    hdrs=(
        Style("""
            :root {
                --bg-primary: #f8fafc;
                --bg-secondary: #ffffff;
                --text-primary: #0f172a;
                --text-secondary: #475569;
                --accent-color: #4f46e5;
                --highlight-bg: rgba(79, 70, 229, 0.15);
                --highlight-border: #6366f1;
                --word-highlight: #d97706;
                --font-size: 1.1rem;
            }
            body.dark-theme {
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --accent-color: #6366f1;
                --highlight-bg: rgba(99, 102, 241, 0.25);
                --highlight-border: #818cf8;
                --word-highlight: #f59e0b;
            }
            body.sepia-theme {
                --bg-primary: #fbf0d9;
                --bg-secondary: #f3e5ab;
                --text-primary: #5f4b32;
                --text-secondary: #7f6a52;
                --accent-color: #8c6d46;
                --highlight-bg: rgba(140, 109, 70, 0.2);
                --highlight-border: #8c6d46;
                --word-highlight: #b45309;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                background-color: var(--bg-primary);
                color: var(--text-primary);
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            /* Scope EPUB elements to use active theme text colors so imported EPUB styles do not conflict */
            .pane, .pane *, .calibre, .calibre * {
                color: var(--text-primary) !important;
                background-color: transparent !important;
            }
            .header-nav {
                height: 60px;
                background: var(--bg-secondary);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 1.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            }
            .header-title { font-size: 1.25rem; font-weight: 700; color: var(--accent-color) !important; }
            .header-controls { display: flex; gap: 1rem; align-items: center; }
            .btn {
                background: var(--accent-color) !important;
                color: white !important;
                border: none;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: opacity 0.2s;
            }
            .btn:hover { opacity: 0.9; }
            .btn.disabled {
                opacity: 0.4 !important;
                pointer-events: none !important;
                cursor: not-allowed !important;
            }
            .select-input {
                background: var(--bg-primary) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--text-secondary);
                padding: 0.4rem 0.6rem;
                border-radius: 6px;
            }
            .reader-container {
                flex: 1;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
                padding: 1.5rem;
                height: calc(100vh - 110px);
                min-height: 0;
                overflow: hidden;
            }
            .pane-column {
                display: flex;
                flex-direction: column;
                height: 100%;
                min-height: 0;
                overflow: hidden;
            }
            .pane-header {
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-secondary) !important;
                margin-bottom: 0.5rem;
                font-weight: 700;
                padding-bottom: 0.2rem;
                flex-shrink: 0;
            }
            .pane {
                background: var(--bg-secondary) !important;
                border-radius: 12px;
                padding: 2rem;
                overflow-y: scroll;
                height: 100%;
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
                font-size: var(--font-size);
                line-height: 1.8;
                scrollbar-width: thin;
                scrollbar-color: var(--accent-color) var(--bg-primary);
            }
            /* Enhanced visible vertical scrollbars */
            .pane::-webkit-scrollbar {
                width: 8px;
            }
            .pane::-webkit-scrollbar-track {
                background: var(--bg-primary);
                border-radius: 4px;
            }
            .pane::-webkit-scrollbar-thumb {
                background-color: var(--accent-color);
                border-radius: 4px;
            }
            .pane::-webkit-scrollbar-thumb:hover {
                background-color: var(--highlight-border);
            }
            .sentence {
                border-radius: 4px;
                padding: 2px 4px;
                cursor: pointer;
                transition: background-color 0.2s, border-color 0.2s;
                border-bottom: 1px transparent dashed;
            }
            .sentence.active {
                background-color: var(--highlight-bg) !important;
                border-bottom: 2px solid var(--highlight-border) !important;
            }
            .word-token {
                cursor: pointer;
                border-radius: 3px;
                padding: 0 2px;
            }
            .word-token.active-word-exact {
                background-color: var(--word-highlight) !important;
                color: #ffffff !important;
                font-weight: bold;
                border-radius: 3px;
            }
            .word-token.active-word-phrase {
                background-color: rgba(217, 119, 6, 0.3) !important;
                color: var(--text-primary) !important;
                border-bottom: 2px solid var(--word-highlight);
                border-radius: 3px;
            }
            .verb-tooltip {
                position: absolute;
                background: var(--bg-secondary);
                color: var(--text-primary);
                border: 1px solid var(--accent-color);
                border-radius: 8px;
                padding: 0.6rem 0.9rem;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                font-size: 0.85rem;
                max-width: 280px;
                pointer-events: none;
                animation: fadeIn 0.15s ease-in-out;
            }
            .verb-tooltip-infinitive {
                font-weight: 700;
                color: var(--accent-color);
                font-size: 0.95rem;
                margin-bottom: 0.2rem;
            }
            .verb-tooltip-tense {
                color: var(--text-secondary);
                font-size: 0.8rem;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(4px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .footer-nav {
                height: 50px;
                background: var(--bg-secondary);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 1.5rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .loading-overlay {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15, 23, 42, 0.6);
                backdrop-filter: blur(4px);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                color: #ffffff;
                font-family: inherit;
                transition: opacity 0.2s ease;
            }
            .loading-overlay.hidden {
                display: none !important;
            }
            .spinner {
                width: 48px;
                height: 48px;
                border: 5px solid rgba(255, 255, 255, 0.2);
                border-top-color: var(--accent-color);
                border-radius: 50%;
                animation: spin 0.9s linear infinite;
                margin-bottom: 1rem;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        """),
        Script("""
            function showLoading(msg) {
                let overlay = document.getElementById('loading-overlay');
                let textElem = document.getElementById('loading-text');
                if (textElem && msg) textElem.textContent = msg;
                if (overlay) overlay.classList.remove('hidden');
            }

            function setTheme(theme) {
                document.body.className = theme + '-theme';
                localStorage.setItem('reader_theme', theme);
            }
            
            function changeFontSize(delta) {
                let current = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--font-size')) || 1.1;
                let next = Math.max(0.8, Math.min(2.0, current + delta));
                document.documentElement.style.setProperty('--font-size', next + 'rem');
                localStorage.setItem('reader_font_size', next);
            }

            // Restore theme & font size on page flip / reload
            (function initTheme() {
                let savedTheme = localStorage.getItem('reader_theme') || 'light';
                if (document.body) {
                    document.body.className = savedTheme + '-theme';
                }
                let savedFontSize = localStorage.getItem('reader_font_size');
                if (savedFontSize) {
                    document.documentElement.style.setProperty('--font-size', savedFontSize + 'rem');
                }
            })();

            document.addEventListener('DOMContentLoaded', () => {
                let savedTheme = localStorage.getItem('reader_theme') || 'light';
                if (document.body) {
                    document.body.className = savedTheme + '-theme';
                }

                // Sentence and Word Bidirectional Synchronization
                // Track active verb bubble source sentence
                let activeBubbleSentenceSid = null;

                // Bidirectional Sentence Highlighting on Hover across both panes
                document.addEventListener('mouseover', (e) => {
                    let sentElem = e.target ? e.target.closest('.sentence') : null;
                    document.querySelectorAll('.sentence').forEach(el => el.classList.remove('active'));
                    if (sentElem) {
                        let sid = sentElem.getAttribute('data-sid');
                        if (sid) {
                            document.querySelectorAll(`.sentence[data-sid="${sid}"]`).forEach(el => el.classList.add('active'));

                            // Dismiss verb definition bubble if cursor moves to a different sentence
                            if (activeBubbleSentenceSid && activeBubbleSentenceSid !== sid) {
                                document.querySelectorAll('.verb-tooltip').forEach(tip => tip.remove());
                                activeBubbleSentenceSid = null;
                            }
                        }
                    } else if (activeBubbleSentenceSid) {
                        // Dismiss bubble if cursor moves completely outside sentences
                        document.querySelectorAll('.verb-tooltip').forEach(tip => tip.remove());
                        activeBubbleSentenceSid = null;
                    }
                });

                document.addEventListener('mouseout', (e) => {
                    if (e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.sentence')) return;
                    document.querySelectorAll('.sentence').forEach(el => el.classList.remove('active'));
                });

                // Word Selection & Sentence Auto-Scroll on Click
                document.addEventListener('click', (e) => {
                    let wordElem = e.target ? e.target.closest('.word-token') : null;
                    let sentElem = e.target ? e.target.closest('.sentence') : null;

                    // Smoothly scroll corresponding sentence in the opposing pane into view if out of bounds
                    if (sentElem) {
                        let sid = sentElem.getAttribute('data-sid');
                        let inLeft = !!sentElem.closest('#left-pane');
                        let oppPane = document.getElementById(inLeft ? 'right-pane' : 'left-pane');
                        if (oppPane && sid) {
                            let oppSent = oppPane.querySelector(`.sentence[data-sid="${sid}"]`);
                            if (oppSent) {
                                let paneRect = oppPane.getBoundingClientRect();
                                let sentRect = oppSent.getBoundingClientRect();
                                if (sentRect.top < paneRect.top || sentRect.bottom > paneRect.bottom) {
                                    oppSent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                                }
                            }
                        }
                    }

                    // Clear previous word highlights and verb tooltips
                    document.querySelectorAll('.word-token').forEach(el => {
                        el.classList.remove('active-word-exact', 'active-word-phrase');
                    });
                    document.querySelectorAll('.verb-tooltip').forEach(tip => tip.remove());

                    if (wordElem) {
                        wordElem.classList.add('active-word-exact');

                        let exactIds = wordElem.getAttribute('data-exact-target-ids');
                        if (exactIds) {
                            exactIds.split(',').forEach(id => {
                                let match = document.getElementById(id);
                                if (match) match.classList.add('active-word-exact');
                            });
                        }

                        let phraseIds = wordElem.getAttribute('data-phrase-target-ids');
                        if (phraseIds) {
                            phraseIds.split(',').forEach(id => {
                                let match = document.getElementById(id);
                                if (match && !match.classList.contains('active-word-exact')) {
                                    match.classList.add('active-word-phrase');
                                }
                            });
                        }

                        // Display verb tooltip popover if clicked word in source pane is a verb
                        if (wordElem.closest('#left-pane')) {
                            let isVerb = wordElem.getAttribute('data-is-verb') === 'true';
                            let infinitive = wordElem.getAttribute('data-infinitive');
                            let tense = wordElem.getAttribute('data-tense');

                            if (isVerb && infinitive) {
                                let sentElem = wordElem.closest('.sentence');
                                activeBubbleSentenceSid = sentElem ? sentElem.getAttribute('data-sid') : null;

                                let tooltip = document.createElement('div');
                                tooltip.className = 'verb-tooltip';
                                tooltip.innerHTML = `<div class="verb-tooltip-infinitive">Root: ${infinitive}</div>` +
                                                    (tense ? `<div class="verb-tooltip-tense">${tense}</div>` : '');
                                document.body.appendChild(tooltip);

                                let rect = wordElem.getBoundingClientRect();
                                tooltip.style.left = Math.max(10, rect.left + window.scrollX) + 'px';
                                tooltip.style.top = (rect.bottom + window.scrollY + 6) + 'px';
                            }
                        }
                    } else {
                        activeBubbleSentenceSid = null;
                    }
                });

                // Left and Right arrow key navigation
                document.addEventListener('keydown', (e) => {
                    // Ignore key events when user is typing in form inputs / selects
                    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

                    if (e.key === 'ArrowLeft') {
                        let prevBtn = document.getElementById('prev-btn');
                        if (prevBtn && prevBtn.href && !prevBtn.classList.contains('disabled')) {
                            e.preventDefault();
                            prevBtn.click();
                        }
                    } else if (e.key === 'ArrowRight') {
                        let nextBtn = document.getElementById('next-btn');
                        if (nextBtn && nextBtn.href && !nextBtn.classList.contains('disabled')) {
                            e.preventDefault();
                            nextBtn.click();
                        }
                    }
                });
            });
        """)
    )
)

aligner = AlignmentEngine()

def get_available_epubs():
    return [f for f in os.listdir('.') if f.endswith('.epub')]

@rt('/')
def get(book: str = None, chapter_idx: int = 0):
    epubs = get_available_epubs()
    selected_book = book if book and book in epubs else (epubs[0] if epubs else None)
    
    chapters = []
    current_sentences = []
    tokens_used = 0
    detected_language = "English"
    epub_css = ""
    if selected_book:
        chapters = extract_chapters_from_epub(selected_book)
        if chapters and 0 <= chapter_idx < len(chapters):
            chap = chapters[chapter_idx]
            epub_css = chap.get("css", "")
            blocks_info = chap.get("blocks", [])
            all_src_sentences = []
            sentence_meta = []
            
            for b in blocks_info:
                p_text = b["text"]
                tag_name = b["tag"]
                cls_list = b.get("class", [])
                style_str = b.get("style", "")
                s_list = split_into_sentences(p_text)
                for idx_s, s_str in enumerate(s_list):
                    all_src_sentences.append(s_str)
                    sentence_meta.append({
                        "is_first_in_block": (idx_s == 0),
                        "is_last_in_block": (idx_s == len(s_list) - 1),
                        "tag": tag_name,
                        "class": " ".join(cls_list) if isinstance(cls_list, list) else str(cls_list),
                        "style": style_str
                    })
            
            # Align via Gemini / cache for complete chapter
            aligned_blocks, tokens_used, detected_lang = aligner.align_sentences_batch(all_src_sentences)
            current_sentences = aligned_blocks
            detected_language = detected_lang

    # Render DOM structure with block-level HTML tag preservation
    src_blocks_html = []
    tgt_blocks_html = []

    current_src_sentences = []
    current_tgt_sentences = []
    current_meta = None

    for idx, block in enumerate(current_sentences):
        sid = f"s_{idx}"
        src_text = block.get("src", "")
        tgt_text = block.get("tgt", "")
        alignments = block.get("word_alignments", [])
        meta = sentence_meta[idx] if idx < len(sentence_meta) else {"is_first_in_block": True, "is_last_in_block": True, "tag": "p", "class": "", "style": ""}

        if meta["is_first_in_block"]:
            current_meta = meta
            current_src_sentences = []
            current_tgt_sentences = []

        # Build interactive tokens
        src_words = src_text.split()
        tgt_words = tgt_text.split()

        def normalize_word(word_str):
            return re.sub(r'^\W+|\W+$', '', word_str).lower()

        norm_src_words = [normalize_word(w) for w in src_words]
        norm_tgt_words = [normalize_word(w) for w in tgt_words]

        # Pre-map token alignment data
        src_to_exact = [[] for _ in range(len(src_words))]
        src_to_phrase = [[] for _ in range(len(src_words))]
        tgt_to_exact = [[] for _ in range(len(tgt_words))]
        tgt_to_phrase = [[] for _ in range(len(tgt_words))]
        src_verbs = [None for _ in range(len(src_words))]

        src_cursor = 0
        tgt_cursor = 0

        for align in alignments:
            raw_src_items = align.get("src_words", [])
            raw_tgt_items = align.get("tgt_words", [])
            align_src_tokens = [w for item in raw_src_items for w in item.split()]
            align_tgt_tokens = [w for item in raw_tgt_items for w in item.split()]
            norm_align_src = [normalize_word(w) for w in align_src_tokens if normalize_word(w)]
            norm_align_tgt = [normalize_word(w) for w in align_tgt_tokens if normalize_word(w)]

            matched_src_indices = []
            if norm_align_src:
                c = src_cursor
                while c <= len(src_words) - len(norm_align_src):
                    if norm_src_words[c : c + len(norm_align_src)] == norm_align_src:
                        matched_src_indices = list(range(c, c + len(norm_align_src)))
                        src_cursor = c + len(norm_align_src)
                        break
                    c += 1
                if not matched_src_indices:
                    c = 0
                    while c <= len(src_words) - len(norm_align_src):
                        if norm_src_words[c : c + len(norm_align_src)] == norm_align_src:
                            matched_src_indices = list(range(c, c + len(norm_align_src)))
                            break
                        c += 1

            matched_tgt_indices = []
            if norm_align_tgt:
                c = tgt_cursor
                while c <= len(tgt_words) - len(norm_align_tgt):
                    if norm_tgt_words[c : c + len(norm_align_tgt)] == norm_align_tgt:
                        matched_tgt_indices = list(range(c, c + len(norm_align_tgt)))
                        tgt_cursor = c + len(norm_align_tgt)
                        break
                    c += 1
                if not matched_tgt_indices:
                    c = 0
                    while c <= len(tgt_words) - len(norm_align_tgt):
                        if norm_tgt_words[c : c + len(norm_align_tgt)] == norm_align_tgt:
                            matched_tgt_indices = list(range(c, c + len(norm_align_tgt)))
                            break
                        c += 1

            if matched_src_indices and matched_tgt_indices:
                is_verb = align.get("is_verb")
                verb_dict = {
                    "infinitive": align.get("infinitive", ""),
                    "tense_person": align.get("tense_person", "")
                } if is_verb else None

                for si in matched_src_indices:
                    if verb_dict and not src_verbs[si]:
                        src_verbs[si] = verb_dict
                    for ti in matched_tgt_indices:
                        tid = f"{sid}_tgt_{ti}"
                        sid_elem = f"{sid}_src_{si}"
                        if norm_src_words[si] == norm_tgt_words[ti]:
                            src_to_exact[si].append(tid)
                            tgt_to_exact[ti].append(sid_elem)
                        else:
                            src_to_phrase[si].append(tid)
                            tgt_to_phrase[ti].append(sid_elem)

        src_tokens_html = []
        for w_idx, w in enumerate(src_words):
            wid = f"{sid}_src_{w_idx}"
            exact_ids = set(src_to_exact[w_idx])
            phrase_ids = set(src_to_phrase[w_idx]) - exact_ids
            token_kwargs = {
                "id": wid,
                "cls": "word-token",
                "data_exact_target_ids": ",".join(exact_ids),
                "data_phrase_target_ids": ",".join(phrase_ids)
            }
            v = src_verbs[w_idx]
            if v:
                token_kwargs["data_is_verb"] = "true"
                token_kwargs["data_infinitive"] = v["infinitive"]
                token_kwargs["data_tense"] = v["tense_person"]

            src_tokens_html.append(Span(w + " ", **token_kwargs))

        tgt_tokens_html = []
        for t_idx, tw in enumerate(tgt_words):
            tid = f"{sid}_tgt_{t_idx}"
            exact_ids = set(tgt_to_exact[t_idx])
            phrase_ids = set(tgt_to_phrase[t_idx]) - exact_ids
            tgt_tokens_html.append(
                Span(
                    tw + " ",
                    id=tid,
                    cls="word-token",
                    data_exact_target_ids=",".join(exact_ids),
                    data_phrase_target_ids=",".join(phrase_ids)
                )
            )

        s_src_elem = Span(*src_tokens_html, cls="sentence", data_sid=sid)
        s_tgt_elem = Span(*tgt_tokens_html, cls="sentence", data_sid=sid)

        current_src_sentences.append(s_src_elem)
        current_src_sentences.append(" ")
        current_tgt_sentences.append(s_tgt_elem)
        current_tgt_sentences.append(" ")

        if meta["is_last_in_block"] or idx == len(current_sentences) - 1:
            tag_type = current_meta["tag"] if current_meta else "p"
            tag_class = current_meta.get("class", "") if current_meta else ""
            tag_style = current_meta.get("style", "") if current_meta else ""

            # Construct FastHTML element matching original tag
            tag_func = globals().get(tag_type.capitalize(), P)
            if tag_type.lower() == 'div':
                tag_func = Div
            elif tag_type.lower() == 'p':
                tag_func = P
            elif tag_type.lower() == 'h1':
                tag_func = H1
            elif tag_type.lower() == 'h2':
                tag_func = H2
            elif tag_type.lower() == 'h3':
                tag_func = H3
            elif tag_type.lower() == 'h4':
                tag_func = H4
            elif tag_type.lower() == 'h5':
                tag_func = H5
            elif tag_type.lower() == 'h6':
                tag_func = H6

            src_blocks_html.append(tag_func(*current_src_sentences, cls=tag_class, style=tag_style))
            tgt_blocks_html.append(tag_func(*current_tgt_sentences, cls=tag_class, style=tag_style))

    prev_chap = max(0, chapter_idx - 1)
    next_chap = min(len(chapters) - 1, chapter_idx + 1) if chapters else 0
    current_chapter_title = chapters[chapter_idx].get("title", f"Section {chapter_idx + 1}") if chapters and 0 <= chapter_idx < len(chapters) else "No chapters loaded"

    return Title("Side-by-Side Reader"), Body(
        Style(epub_css),
        Div(
            Div(cls="spinner"),
            Div("Translating & Aligning Section with Gemini...", id="loading-text", style="font-weight: 600; font-size: 1.1rem;"),
            cls="loading-overlay hidden",
            id="loading-overlay"
        ),
        Div(
            Div("Side-by-Side Reader", cls="header-title"),
            Div(
                Select(
                    *[Option(b, value=b, selected=(b == selected_book)) for b in epubs],
                    onchange="showLoading('Loading Book...'); window.location.href='/?book=' + encodeURIComponent(this.value)",
                    cls="select-input"
                ),
                Select(
                    *[Option(chapters[i].get("title", f"Section {i+1}"), value=i, selected=(i == chapter_idx)) for i in range(len(chapters))],
                    onchange=f"showLoading('Translating Section with Gemini...'); window.location.href='/?book=' + encodeURIComponent('{selected_book}') + '&chapter_idx=' + this.value",
                    cls="select-input"
                ) if chapters else "",
                Button("Dark", onclick="setTheme('dark')", cls="btn"),
                Button("Light", onclick="setTheme('light')", cls="btn"),
                Button("Sepia", onclick="setTheme('sepia')", cls="btn"),
                Button("A-", onclick="changeFontSize(-0.1)", cls="btn"),
                Button("A+", onclick="changeFontSize(0.1)", cls="btn"),
                cls="header-controls"
            ),
            cls="header-nav"
        ),
        Div(
            Div(
                Div(f"Original Text ({detected_language})", cls="pane-header"),
                Div(
                    Div(*src_blocks_html),
                    cls="pane calibre",
                    id="left-pane"
                ),
                cls="pane-column"
            ),
            Div(
                Div("English Translation", cls="pane-header"),
                Div(
                    Div(*tgt_blocks_html),
                    cls="pane calibre",
                    id="right-pane"
                ),
                cls="pane-column"
            ),
            cls="reader-container"
        ),
        Div(
            A("Previous Section", id="prev-btn", href=f"/?book={selected_book}&chapter_idx={prev_chap}" if chapter_idx > 0 else None, onclick="showLoading('Translating & Aligning Section with Gemini...')" if chapter_idx > 0 else None, cls=f"btn {'disabled' if chapter_idx <= 0 else ''}"),
            Div(
                Span(f"Language: {detected_language}", id="status-language", style="font-weight: 600; margin-right: 8px;"),
                Span(
                    f"• {current_chapter_title} of {len(chapters)}" if current_chapter_title.startswith("Section ") else f"• {current_chapter_title} ({chapter_idx + 1} of {len(chapters)})"
                    if chapters else "• No chapters loaded",
                    id="status-chapter-title"
                ),
                Span(f" • {aligner.model_name} tokens: {tokens_used:,}" if tokens_used else f" • {aligner.model_name} tokens: 0", style="margin-left: 8px; opacity: 0.8;"),
                style="display: flex; align-items: center;"
            ),
            A("Next Section", id="next-btn", href=f"/?book={selected_book}&chapter_idx={next_chap}" if chapter_idx < len(chapters) - 1 else None, onclick="showLoading('Translating & Aligning Section with Gemini...')" if chapter_idx < len(chapters) - 1 else None, cls=f"btn {'disabled' if chapter_idx >= len(chapters) - 1 else ''}"),
            cls="footer-nav"
        )
    )

if __name__ == "__main__":
    serve()
