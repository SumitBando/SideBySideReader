import os
import json
import hashlib
import re
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

STOPWORDS_BY_LANG = {
    'Italian': {
        'della', 'dello', 'degli', 'delle', 'nella', 'nello', 'negli', 'nelle',
        'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
        'anche', 'perché', 'più', 'sono', 'essere', 'stato', 'stata', 'stati', 'state',
        'aveva', 'avevano', 'hanno', 'fare', 'tutto', 'tutti', 'tutta', 'tutte',
        'molto', 'molti', 'molta', 'molte', 'quando', 'come', 'cosa', 'loro', 'ogni',
        'sempre', 'dopo', 'prima', 'mentre', 'qualche', 'ancora', 'allora', 'senza',
        'capitolo', 'giorno', 'anni', 'uomo', 'donna', 'casa', 'lui', 'lei', 'noi',
        'voi', 'mio', 'mia', 'miei', 'mie', 'tuo', 'tua', 'tuoi', 'tue', 'suo',
        'sua', 'suoi', 'sue', 'nostro', 'nostra', 'vostro', 'vostra', 'ciao', 'storia',
        'del', 'dei', 'nel', 'nei', 'era', 'erano', 'con', 'per', 'tra', 'fra'
    },
    'Spanish': {
        'los', 'las', 'del', 'una', 'unos', 'unas', 'este', 'esta', 'estos',
        'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas',
        'también', 'porque', 'más', 'pero', 'como', 'cuando', 'donde', 'quien',
        'quienes', 'había', 'habían', 'hacer', 'todo', 'todos', 'toda', 'todas',
        'mucho', 'muchos', 'mucha', 'muchas', 'siempre', 'nunca', 'después', 'antes',
        'mientras', 'alguno', 'alguna', 'algunos', 'algunas', 'todavía', 'entonces',
        'capítulo', 'hombre', 'mujer', 'casa', 'años', 'tiempo', 'vida', 'mundo',
        'dijo', 'decía', 'él', 'ella', 'ellos', 'ellas', 'nosotros', 'nosotras',
        'nuestro', 'nuestra', 'nuestros', 'nuestras', 'cuento', 'cuentos', 'libro',
        'fue', 'eran', 'para', 'con', 'por', 'entre', 'hacia', 'desde'
    },
    'French': {
        'les', 'des', 'une', 'dans', 'pour', 'avec', 'sur', 'est', 'sont', 'cet',
        'cette', 'ces', 'mais', 'plus', 'pas', 'elle', 'ils', 'elles', 'nous',
        'vous', 'leur', 'leurs', 'tout', 'tous', 'toute', 'toutes', 'comme', 'faire',
        'être', 'avoir', 'aussi', 'très', 'quand', 'après', 'avant', 'pendant',
        'toujours', 'jamais'
    },
    'German': {
        'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem',
        'einer', 'eines', 'und', 'von', 'mit', 'auf', 'für', 'ist', 'sind', 'war',
        'waren', 'nicht', 'als', 'auch', 'ich', 'wir', 'ihr', 'sie', 'nach', 'wie',
        'bei', 'über', 'hatte', 'hatten', 'haben', 'werden', 'wurde', 'wurden',
        'kann', 'können', 'müssen', 'soll', 'sollen'
    },
    'Portuguese': {
        'os', 'as', 'uma', 'uns', 'umas', 'do', 'da', 'dos', 'das', 'no', 'na',
        'nos', 'nas', 'para', 'com', 'por', 'como', 'seu', 'sua', 'seus', 'suas',
        'são', 'foi', 'mas', 'mais', 'não', 'ele', 'ela', 'eles', 'elas', 'nós',
        'quando', 'muito', 'também'
    },
    'English': {
        'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but',
        'his', 'from', 'they', 'say', 'her', 'she', 'will', 'one', 'all', 'would',
        'there', 'their', 'what', 'about', 'which', 'when', 'make', 'can', 'like',
        'time', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
        'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
        'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after',
        'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new',
        'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'chapter',
        'introduction', 'book', 'short', 'stories', 'reading', 'beginner', 'learn'
    }
}

def detect_language(sentences: List[str]) -> str:
    """Identifies the primary non-English language of the input sentences, or English if purely English."""
    combined_text = ' '.join(sentences)
    if not combined_text.strip():
        return 'English'
    if re.search(r'[\u0400-\u04FF]', combined_text):
        return 'Russian'
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', combined_text):
        return 'Japanese'
    if re.search(r'[\u4E00-\u9FFF]', combined_text):
        return 'Chinese'

    words = re.findall(r'\b[^\W\d_]+\b', combined_text.lower(), re.UNICODE)
    if not words:
        return 'English'

    scores = {}
    for lang, sw in STOPWORDS_BY_LANG.items():
        score = sum(1 for w in words if w in sw)
        scores[lang] = score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_lang, best_score = sorted_scores[0]

    if best_score == 0:
        return 'English'

    # If English is highest but a non-English language has significant presence (e.g., bilingual sections)
    non_en_scores = [item for item in sorted_scores if item[0] != 'English']
    if non_en_scores and non_en_scores[0][1] > 0:
        if best_lang == 'English' and non_en_scores[0][1] >= 2 and non_en_scores[0][1] >= best_score * 0.2:
            return non_en_scores[0][0]

    return best_lang

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

    def align_sentences_batch(self, sentences: List[str], tgt_lang: str = "English", batch_size: int = 25) -> Tuple[List[Dict[str, Any]], int, str]:
        if not sentences:
            return [], 0, "Unknown"

        if len(sentences) <= batch_size:
            return self._align_single_batch(sentences, tgt_lang)

        all_blocks = []
        total_tokens = 0
        detected_languages = []

        for i in range(0, len(sentences), batch_size):
            chunk = sentences[i:i + batch_size]
            chunk_blocks, chunk_tokens, chunk_lang = self._align_single_batch(chunk, tgt_lang)
            all_blocks.extend(chunk_blocks)
            total_tokens += chunk_tokens
            if chunk_lang:
                detected_languages.append(chunk_lang)

        # Primary detected language (prioritize non-English if present)
        non_en_langs = [l for l in detected_languages if l != "English"]
        final_lang = non_en_langs[0] if non_en_langs else (detected_languages[0] if detected_languages else "English")
        return all_blocks, total_tokens, final_lang

    def _align_single_batch(self, sentences: List[str], tgt_lang: str = "English") -> Tuple[List[Dict[str, Any]], int, str]:
        if not sentences:
            return [], 0, "Unknown"

        cache_key = self._get_cache_key(sentences)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict) and "blocks" in content:
                        detected_lang = content.get("detected_language") or detect_language(sentences)
                        return content["blocks"], content.get("total_tokens", 0), detected_lang
                    elif isinstance(content, list):
                        return content, 0, detect_language(sentences)
            except Exception:
                pass

        # Fallback dictionary/translator aligner if Gemini API Key not present or API call fails
        if not self.client:
            blocks = self._fallback_align(sentences)
            detected_lang = detect_language(sentences)
            return blocks, 0, detected_lang

        prompt = f"""You are an expert multi-language translation and alignment engine.
1. Identify the primary non-English language of the input text (e.g., 'Spanish', 'Italian', 'French', 'German', 'Portuguese', 'Russian', etc.). If the text is purely in English, set "detected_language" to "English".
2. Translate all non-English sentences into {tgt_lang}.
   Note: If a sentence or block is ALREADY in {tgt_lang} (English), keep "tgt" identical to "src" as is — DO NOT translate it into any other language.

3. For each sentence, provide:
   - "src": Original sentence as given
   - "tgt": English translation (or original text if already in English)
   - "word_alignments": Word and phrase correspondences between original words ("src_words") and English words ("tgt_words").
   - If a source word/phrase includes a verb in the source language, also provide:
     "is_verb": true,
     "infinitive": "root verb in infinitive form in that source language",
     "tense_person": "subject, tense, and mood description"

List of sentences:
{json.dumps(sentences, ensure_ascii=False)}

Respond ONLY with valid JSON with the following structure:
{{
  "detected_language": "Detected non-English language (e.g. Italian, Spanish, French) or English",
  "blocks": [
    {{
      "src": "sentence in source language",
      "tgt": "sentence in English",
      "word_alignments": [
         {{
           "src_words": ["..."],
           "tgt_words": ["..."],
           "is_verb": true,
           "infinitive": "...",
           "tense_person": "..."
         }}
      ]
    }}
  ]
}}
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

            blocks = []
            detected_language = "English"
            if isinstance(data, dict):
                blocks = data.get("blocks", [])
                detected_language = data.get("detected_language") or detect_language(sentences)
            elif isinstance(data, list):
                blocks = data
                detected_language = detect_language(sentences)

            cache_data = {
                "detected_language": detected_language,
                "blocks": blocks,
                "total_tokens": total_tokens_used
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            return blocks, total_tokens_used, detected_language
        except Exception as e:
            print(f"Gemini API alignment fallback due to error: {e}")
            blocks = self._fallback_align(sentences)
            detected_lang = detect_language(sentences)
            return blocks, 0, detected_lang

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
            
            # Positional word alignment mapping
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
    blocks, tokens, lang = engine.align_sentences_batch(test_sentences)
    print("Detected language:", lang)
    print("Alignment result count:", len(blocks))
    print("Sample translation:", blocks[0]["tgt"] if blocks else "")

