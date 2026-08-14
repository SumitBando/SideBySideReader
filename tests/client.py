import urllib.request
import json
import os
import sys
import re
from bs4 import BeautifulSoup

def test_section_one_word_alignments():
    url = "http://localhost:5001/?book=Yo%20mat%C3%A9%20a%20Kennedy%20-%C2%A0V%C3%A1zquez%20Montalb%C3%A1n,%20Manuel%20-%C2%A01971.epub&chapter_idx=0"
    try:
        req = urllib.request.urlopen(url)
        assert req.status == 200, f"Expected 200 OK status, got {req.status}"
        html_content = req.read().decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')

        left_pane = soup.find('div', id='left-pane')
        right_pane = soup.find('div', id='right-pane')
        assert left_pane is not None, "Left pane missing"
        assert right_pane is not None, "Right pane missing"

        src_tokens = left_pane.find_all('span', class_='word-token')
        tgt_tokens = right_pane.find_all('span', class_='word-token')
        print(f"[TEST] Extracted {len(src_tokens)} Spanish source tokens and {len(tgt_tokens)} English target tokens from Section 1.")

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

        print(f"[TEST] Tested all Spanish tokens in Section 1. Total valid target ID pairs: {valid_mappings}, Errors found: {len(errors)}")

        if errors:
            for err in errors[:10]:
                print(f"  [ERROR] {err}")
            return False

        print("[SUCCESS] All Spanish word tokens in Section 1 map strictly to valid sequence pairs in the English pane!")
        return True

    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_section_one_word_alignments()
    if not success:
        sys.exit(1)
