import urllib.request
import urllib.parse
import sys
import os
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_page_content(path: str) -> str:
    url = f"http://localhost:5001{path}"
    try:
        req = urllib.request.urlopen(url)
        if req.status == 200:
            return req.read().decode('utf-8')
    except Exception:
        pass
    
    # Fallback to TestClient if standalone server not active
    from starlette.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get(path)
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    return resp.text

def test_language_and_word_alignments(book_name: str, chapter_idx: int, expected_language: str):
    path = f"/?book={urllib.parse.quote(book_name)}&chapter_idx={chapter_idx}"
    try:
        html_content = get_page_content(path)
        soup = BeautifulSoup(html_content, 'html.parser')

        left_pane = soup.find('div', id='left-pane')
        right_pane = soup.find('div', id='right-pane')
        assert left_pane is not None, "Left pane missing"
        assert right_pane is not None, "Right pane missing"

        # Verify bottom status bar language and chapter title display
        status_lang_elem = soup.find('span', id='status-language')
        assert status_lang_elem is not None, "Bottom status bar language element missing"
        status_lang_text = status_lang_elem.get_text().strip()
        print(f"[TEST] Bottom status bar language: '{status_lang_text}' (Expected: 'Language: {expected_language}')")
        assert f"Language: {expected_language}" in status_lang_text, f"Expected 'Language: {expected_language}' in status bar, got '{status_lang_text}'"

        status_title_elem = soup.find('span', id='status-chapter-title')
        assert status_title_elem is not None, "Bottom status bar chapter title missing"
        print(f"[TEST] Bottom status bar chapter title: '{status_title_elem.get_text().strip()}'")

        # Verify chapter select options have actual chapter names
        options = [opt.get_text().strip() for opt in soup.find_all('option')]
        non_generic_options = [opt for opt in options if not opt.startswith('Section ') and len(opt) > 0]
        print(f"[TEST] Found {len(options)} total options, {len(non_generic_options)} named chapters in dropdown.")
        assert len(non_generic_options) > 0, "Expected actual chapter titles in select options"

        # Verify left pane header indicates detected language
        pane_header = soup.find('div', class_='pane-header')
        assert pane_header is not None, "Pane header missing"
        print(f"[TEST] Left pane header: '{pane_header.get_text().strip()}'")
        assert expected_language in pane_header.get_text(), f"Expected '{expected_language}' in pane header, got '{pane_header.get_text()}'"

        src_tokens = left_pane.find_all('span', class_='word-token')
        tgt_tokens = right_pane.find_all('span', class_='word-token')
        print(f"[TEST] Extracted {len(src_tokens)} source tokens ({expected_language}) and {len(tgt_tokens)} English target tokens.")

        tgt_ids_set = set(t.get('id') for t in tgt_tokens)

        errors = []
        valid_mappings = 0

        for token in src_tokens:
            token_id = token.get('id')
            token_text = token.get_text().strip()
            exact_attr = token.get('data-exact-target-ids', '')
            phrase_attr = token.get('data-phrase-target-ids', '')
            
            target_ids = (exact_attr + ',' + phrase_attr).strip(',').split(',')
            for tid in target_ids:
                if tid and tid not in tgt_ids_set:
                    errors.append(f"Token '{token_text}' ({token_id}) references non-existent target ID '{tid}'")
                elif tid:
                    valid_mappings += 1

        print(f"[TEST] Tested all tokens for {expected_language}. Total valid target ID pairs: {valid_mappings}, Errors found: {len(errors)}")

        if errors:
            for err in errors[:10]:
                print(f"  [ERROR] {err}")
            return False

        print(f"[SUCCESS] All {expected_language} word tokens map strictly to valid sequence pairs in the English pane!")
        return True

    except Exception as e:
        print(f"[FAIL] Test error on {book_name} (Section {chapter_idx}): {e}")
        return False

def run_all_tests():
    print("=== Running Smoke Tests ===")
    # 1. Spanish Book Test
    spanish_book = "Yo maté a Kennedy - Vázquez Montalbán, Manuel - 1971.epub"
    es_ok = test_language_and_word_alignments(spanish_book, chapter_idx=0, expected_language="Spanish")
    if not es_ok:
        return False

    print("\n--------------------------------------------------\n")

    # 2. Italian Book Test
    italian_book = "Italian Short Stories for Beginners - Richards, Olly - 2016.epub"
    it_ok = test_language_and_word_alignments(italian_book, chapter_idx=11, expected_language="Italian")
    if not it_ok:
        return False

    print("\n[ALL TESTS PASSED] Multi-language detection, status bar display, and dual alignment verified!")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)

