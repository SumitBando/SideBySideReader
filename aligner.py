import os
import json
import hashlib
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

class AlignmentEngine:
    def __init__(self, cache_dir: str = "cache", model_name: str = None):
        self.cache_dir = cache_dir
        self.model_name = model_name or os.environ.get("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")
        os.makedirs(cache_dir, exist_ok=True)
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if genai and api_key else None

    def _get_cache_key(self, sentences: List[str]) -> str:
        content = "||".join(sentences)
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def align_sentences_batch(self, sentences: List[str], src_lang: str = "Spanish", tgt_lang: str = "English") -> List[Dict[str, Any]]:
        if not sentences:
            return [], 0

        cache_key = self._get_cache_key(sentences)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict) and "blocks" in content:
                        return content["blocks"], content.get("total_tokens", 0)
                    elif isinstance(content, list):
                        return content, 0
            except Exception:
                pass

        # Fallback dictionary/dummy aligner if Gemini API Key not present or API call fails
        if not self.client:
            return self._fallback_align(sentences), 0

        prompt = f"""You are an expert dual-language alignment engine. Translate the following list of sentences into {tgt_lang}.
Note: If a sentence or block is ALREADY in {tgt_lang} (English), keep "tgt" identical to "src" as is — DO NOT translate it into {src_lang} or any other language.

For each sentence, provide:
1. "src": Original sentence as given
2. "tgt": English translation (or original text if already in English)
3. "word_alignments": Word and phrase correspondences between original words ("src_words") and English words ("tgt_words").
   - If a source word/phrase includes a verb in {src_lang}, also provide:
     "is_verb": true,
     "infinitive": "root verb in infinitive form (e.g., asistir, comer, ser)",
     "tense_person": "subject, tense, and mood description (e.g. 1st person plural (nosotros), present indicative)"

List of sentences:
{json.dumps(sentences, ensure_ascii=False)}

Respond ONLY with valid JSON with the following structure:
[
  {{
    "src": "sentence in source language",
    "tgt": "sentence in English",
    "word_alignments": [
       {{
         "src_words": ["asistimos"],
         "tgt_words": ["we", "witness"],
         "is_verb": true,
         "infinitive": "asistir",
         "tense_person": "1st person plural (nosotros), present indicative"
       }}
    ]
  }}
]
"""
        total_tokens_used = 0
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                total_tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)

            cache_data = {
                "blocks": data,
                "total_tokens": total_tokens_used
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            return data, total_tokens_used
        except Exception as e:
            print(f"Gemini API alignment fallback due to error: {e}")
            blocks = self._fallback_align(sentences)
            return blocks, 0

    def _fallback_align(self, sentences: List[str]) -> List[Dict[str, Any]]:
        # Free online translation fallback when GEMINI_API_KEY is not configured
        results = []
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target='en')
        except Exception:
            translator = None

        for s in sentences:
            if translator:
                try:
                    tgt_sentence = translator.translate(s)
                except Exception:
                    tgt_sentence = s
            else:
                tgt_sentence = s

            src_words = [w for w in s.split() if w]
            tgt_words = [w for w in tgt_sentence.split() if w]
            alignments = []
            
            # Simple positional word alignment mapping
            for idx, sw in enumerate(src_words):
                if idx < len(tgt_words):
                    tw = tgt_words[idx]
                    alignments.append({
                        "src_words": [sw],
                        "tgt_words": [tw]
                    })

            results.append({
                "src": s,
                "tgt": tgt_sentence,
                "word_alignments": alignments
            })
        return results

if __name__ == "__main__":
    engine = AlignmentEngine()
    test_sentences = [
        "Yo maté a Kennedy en una tarde de verano.",
        "El presidente estaba en Dallas."
    ]
    res = engine.align_sentences_batch(test_sentences)
    print("Alignment result count:", len(res))
    print("Sample translation:", res[0]["tgt"] if res else "")
