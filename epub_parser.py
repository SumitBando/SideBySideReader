import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString

def extract_chapters_from_epub(epub_path: str):
    book = epub.read_epub(epub_path)
    chapters = []
    
    # Extract embedded stylesheets
    css_content = ""
    for item in book.get_items_of_type(ebooklib.ITEM_STYLE):
        try:
            css_content += item.get_content().decode('utf-8') + "\n"
        except Exception:
            pass

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
            chapters.append({
                "id": item.get_name(),
                "title": item.get_name().rsplit('/', 1)[-1],
                "blocks": blocks,
                "paragraphs": [b["text"] for b in blocks],
                "css": css_content
            })
            
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
