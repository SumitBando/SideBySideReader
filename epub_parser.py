import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString

from functools import lru_cache

def build_toc_map(book):
    toc_map = {}
    def parse_toc(items):
        for it in items:
            if isinstance(it, tuple) or isinstance(it, list):
                if len(it) > 0:
                    if hasattr(it[0], 'href') and hasattr(it[0], 'title'):
                        clean_href = it[0].href.split('#')[0]
                        toc_map[clean_href] = it[0].title
                        toc_map[clean_href.rsplit('/', 1)[-1]] = it[0].title
                if len(it) > 1 and isinstance(it[1], (list, tuple)):
                    parse_toc(it[1])
            elif hasattr(it, 'href') and hasattr(it, 'title'):
                clean_href = it.href.split('#')[0]
                toc_map[clean_href] = it.title
                toc_map[clean_href.rsplit('/', 1)[-1]] = it.title
    try:
        parse_toc(book.toc)
    except Exception:
        pass
    return toc_map

def extract_chapter_title(soup, item_name: str, idx: int, toc_map: dict, blocks: list) -> str:
    # 1. TOC lookup
    clean_name = item_name.split('#')[0]
    base_name = clean_name.rsplit('/', 1)[-1]
    if clean_name in toc_map and toc_map[clean_name].strip():
        return ' '.join(toc_map[clean_name].split())
    if base_name in toc_map and toc_map[base_name].strip():
        return ' '.join(toc_map[base_name].split())

    # 2. Heading tags (h1-h6)
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        htext = ' '.join(h.get_text().split()).strip()
        if htext and len(htext) <= 80:
            return htext

    # 3. Known title patterns or short first block
    if blocks:
        first_text = ' '.join(blocks[0]['text'].split()).strip()
        title_pattern = re.compile(
            r'^(cap[ií]tulo\s+\d+|chapter\s+\d+|anness[oi]|anexo|domande|preguntas|soluzioni|soluciones|\d+\.\s+[A-Z\u00C0-\u00FF]|racconti|cuentos|preface|introduction|acerca de|fuentes|serie|notas|nota|about|copyright|epilogue|prologue|contents|table of contents|free masterclass|other books)',
            re.IGNORECASE
        )
        if title_pattern.search(first_text) and len(first_text) <= 80:
            return first_text

        if len(first_text) <= 50 and not first_text.endswith(('.', '!', '?')) and '\n' not in first_text:
            return first_text

    return f"Section {idx + 1}"

@lru_cache(maxsize=32)
def extract_chapters_from_epub(epub_path: str):
    book = epub.read_epub(epub_path)
    chapters = []
    toc_map = build_toc_map(book)
    
    # Extract embedded stylesheets
    css_content = ""
    for item in book.get_items_of_type(ebooklib.ITEM_STYLE):
        try:
            css_content += item.get_content().decode('utf-8') + "\n"
        except Exception:
            pass

    doc_idx = 0
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # Remove script/style/head tags
        for elem in soup(['script', 'style', 'head']):
            elem.decompose()
            
        blocks = []
        for p in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote']):
            # Skip container tags if they contain nested block elements to avoid duplicate text extraction
            if p.find(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote']):
                continue
            text = p.get_text().strip()
            if text:
                # Extract HTML classes & inline styles
                blocks.append({
                    "tag": p.name.lower(),
                    "class": p.get("class", []),
                    "style": p.get("style", ""),
                    "text": text
                })
                
        if blocks:
            title = extract_chapter_title(soup, item.get_name(), doc_idx, toc_map, blocks)
            chapters.append({
                "id": item.get_name(),
                "title": title,
                "blocks": blocks,
                "paragraphs": [b["text"] for b in blocks],
                "css": css_content
            })
            doc_idx += 1
            
    return chapters

def split_into_sentences(text: str):
    sentence_endings = re.compile(r'(?<=[.!?¿¡])\s+(?=[A-ZÁÉÍÓÚÑa-z])')
    raw_sentences = sentence_endings.split(text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences

def tokenize_words(sentence: str):
    tokens = []
    raw_tokens = re.findall(r'\w+|[^\w\s]', sentence, re.UNICODE)
    for idx, tok in enumerate(raw_tokens):
        tokens.append({
            "idx": idx,
            "text": tok,
            "is_word": bool(re.match(r'^\w+$', tok, re.UNICODE))
        })
    return tokens

if __name__ == "__main__":
    import os
    epubs = [f for f in os.listdir('.') if f.endswith('.epub')]
    if epubs:
        epub_file = epubs[0]
        print(f"Reading file: {epub_file}")
        chaps = extract_chapters_from_epub(epub_file)
        print(f"Extracted {len(chaps)} document sections.")
        if chaps:
            print("CSS length:", len(chaps[0].get("css", "")))
            print("Sample block:", chaps[0]["blocks"][0] if chaps[0]["blocks"] else "")
