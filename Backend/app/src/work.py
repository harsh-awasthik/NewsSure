"""
============================================================
🧠 TruthScope – AI + Community-Driven News Verification System
============================================================
Unified Workflow:
    1️⃣ Input Handling (Text / Image)
    2️⃣ Image Authenticity Check
    3️⃣ OCR Extraction (if image)
    4️⃣ SERP API Article Retrieval
    5️⃣ Domain Credibility Filtering
    6️⃣ Semantic Similarity Filtering
    7️⃣ Cross Verification (Scraping, Summarization, Classification)
    8️⃣ Final Result Combination
============================================================
"""

# ============================================================
# 🧩 IMPORTS
# ============================================================

import os
import tempfile
from django.http import JsonResponse
import cv2
import numpy as np
import time
import json
import requests
import spacy
import re
import nltk
from bs4 import BeautifulSoup
from newspaper import Article
import trafilatura
import google.generativeai as genai
from transformers import pipeline
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from deep_translator import GoogleTranslator
from langdetect import detect
from paddleocr import PaddleOCR
import http.client
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
from rest_framework.response import Response


# API USED
GEMINI_API = "AIzaSyBvSNiySHFGClevEnIASp7SZapQ0yVCXzo"
SERP_API_KEY = "ea89ee70c31f83aade9cf6d1bfb04cff3f2046976e8cc323515719f801a91ae8"
RAPIDAPI_KEY = "9f93085e44msh4682dc70c41d0b1p15088ajsne1f9b23862ab"
RAPIDAPI_HOST = "media-bias-fact-check-ratings-api2.p.rapidapi.com"
api_user = "1174532159"
api_secret = "KnjsVMQMe7DX8F4jhXqS8Y57a2XUyncy"


# === CONFIG ===
CACHE_FILE = "app/assets/mbfc_data.json"
CACHE_EXPIRY_HOURS = 24*15  # optional - re-fetch after 15 day

# ============================================================
# 🏁 MAIN FUNCTION
# ============================================================
import nltk
for pkg in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{pkg}')
    except LookupError:
        nltk.download(pkg)

def verify_claim(request):
    """
    Handles the complete workflow for claim verification.
    - If image: runs AI detection → OCR extraction → SERP → domain → semantic → cross-verification
    - If text: directly runs SERP → domain → semantic → cross-verification
    """

    input_type = request.data.get('inputType')

    # ============================================================
    # 🖼️ STAGE 1 & 2 – IMAGE VERIFICATION + OCR EXTRACTION
    # ============================================================
    if input_type == 'image':
        image_file = request.FILES.get('file')
        temp_dir = tempfile.gettempdir()  # works on Windows, macOS, Linux
        temp_path = os.path.join(temp_dir, image_file.name)
        # temp_path = f"/tmp/{image_file.name}"
        with open(temp_path, 'wb+') as dest:
            for chunk in image_file.chunks():
                dest.write(chunk)

        # --- Stage 1: Check if AI generated ---
        ai_check = simulate_image_verification(temp_path)
        if ai_check >= 0.10:  # threshold for AI-generated
            return Response({
                "status": "success",
                "claim": "Uploaded image analyzed for AI-generated content",
                "verdict": "mixed",  # You can use "false" or "mixed" if AI-generated
                "truthScore": 0,
                "aiGenerated": True,
                "sources": [
                    {
                        "name": "SightEngine",
                        "credibility": 70,
                        "url": "https://sightengine.com/"
                    }
                ],
                "explanation": "Detected as AI-generated visual. No further verification performed.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        # --- Stage 2: OCR Extraction ---
        extracted_text = run_ocr_extraction(temp_path, visualize=True)
        claim = extracted_text.strip() if extracted_text else "No text found in image."


    # ============================================================
    # 📝 STAGE 3 – TEXT INPUT HANDLING
    # ============================================================
    else:
        claim = request.data.get('input', '').strip()

    if not claim:
        return Response({"error": "No valid text or image content found."}, status=400)

    print(f"\n🧠 CLAIM: {claim}\n{'='*80}")

    # ============================================================
    # 🔎 STAGE 4 – SERP API ARTICLE RETRIEVAL
    # ============================================================
    serp_results = finding_related_article(claim)
    print(f"[INFO] Retrieved {serp_results['total_results']} related articles.")

    # ============================================================
    # 🌐 STAGE 5 – DOMAIN CREDIBILITY CHECK
    # ============================================================
    domain_results = simulate_domain_check(serp_results.get("retrieved_articles"))
    

    # ============================================================
    # 🧠 STAGE 6 – SEMANTIC EMBEDDING + CROSS VERIFICATION
    # ============================================================
    semantic_urls = semantic_embedding(domain_results.get("filtered_articles"), claim) 

    # ============================================================
    # 🧠 STAGE 7 – SEMANTIC EMBEDDING + CROSS VERIFICATION
    # ============================================================
    cross_verification_results = simulate_cross_verification(claim,urls=semantic_urls)

    # ============================================================
    # 🧾 STAGE 8 – FINAL RESULT COMBINATION
    # ============================================================
    result = combine_results(domain_results, cross_verification_results)

    return Response(result)


# ============================================================
# 🔍 STAGE 1 – IMAGE VERIFICATION (AI Generated or Not)
# ============================================================

def simulate_image_verification(image_file):
    """Simulates AI-image authenticity check."""
    params = {
        'models': 'genai',
        'api_user': api_user,
        'api_secret': api_secret
        }
    files = {'media': open(image_file, 'rb')}
    r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)

    output = json.loads(r.text)

    print(json.dumps(output, indent=2))

    return output["type"]["ai_generated"]


# ============================================================
# 📖 STAGE 2 – OCR TEXT EXTRACTION
# ============================================================

def run_ocr_extraction(image_path: str, visualize: bool = False) -> str:
    """Extract text from an image using PaddleOCR, compatible with all versions."""
    print("🚀 Initializing PaddleOCR...")

    ocr = PaddleOCR(lang='en')

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"❌ Image not found: {image_path}")

    try:
        # ✅ For PaddleOCR v4.x (newer)
        img = cv2.imread(image_path)
        results = ocr.predict(img)
    except Exception:
        # ✅ Fallback for older versions
        results = ocr.ocr(image_path)

    all_text = []
    extracted_data = []

    # Newer dict-based output
    if isinstance(results, list) and results and isinstance(results[0], dict):
        for res in results:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            boxes = res.get("rec_polys", [])
            for i in range(len(texts)):
                extracted_data.append({
                    "text": texts[i],
                    "confidence": float(scores[i]),
                    "bbox": np.array(boxes[i]).astype(int).tolist()
                })
                all_text.append(texts[i])
    else:
        # Legacy nested list format
        for line in results:
            for item in line:
                txt = item[1][0]
                conf = float(item[1][1])
                all_text.append(txt)
                extracted_data.append({"text": txt, "confidence": conf})

    extracted_text = " ".join(all_text).strip()
    print(f"🧾 Extracted text: {extracted_text or '⚠️ No text detected.'}")
    return extracted_text



# ============================================================
# 🌎 STAGE 3 – SERP API RELATED ARTICLE SEARCH
# ============================================================

def finding_related_article(claim):
    """Fetch related articles using SERP API."""
    nlp = spacy.load("en_core_web_sm")

    def extract_keywords(text):
        doc = nlp(text)
        keywords = {ent.text for ent in doc.ents}
        keywords |= {t.text for t in doc if t.pos_ in ["NOUN", "PROPN"] and len(t.text) > 2}
        cleaned = [re.sub(r"[^\w\s-]", "", kw).strip() for kw in keywords]
        return " ".join(cleaned)

    query = extract_keywords(claim)
    print(f"[INFO] Optimized search query: {query}")

    articles = []
    for page in range(2):
        start = page * 10
        params = {"engine": "google", "q": query, "num": 10, "start": start, "api_key": SERP_API_KEY}
        try:
            res = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = res.json()
            for i, item in enumerate(data.get("organic_results", [])):
                articles.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "rank": start + i + 1,
                    "source": "SERP_API"
                })
        except Exception as e:
            print(f"[Error] SERP API failed: {e}")
    output =  {
        "claim": claim,
        "optimized_query": query,
        "retrieved_articles": articles,  # [ { "title": "...", "url": "...", ... }, ... ],
        "total_results": len(articles)
    }

    # to see all the searched url with heading 
    # print(output)

    return output


# ============================================================
# 🏛️ STAGE 4 – DOMAIN CREDIBILITY CHECK
# ============================================================

def extract_domain(url_or_domain):
    """
    Extracts clean domain from a URL or domain.
    e.g. https://timesofindia.indiatimes.com/news → indiatimes.com
    """
    url_or_domain = url_or_domain.strip().lower()

    # Parse full URL if needed
    if url_or_domain.startswith("http"):
        parsed = urlparse(url_or_domain)
        hostname = parsed.hostname or ""
    else:
        hostname = url_or_domain

    # Remove leading www.
    if hostname.startswith("www."):
        hostname = hostname[4:]

    # Keep main domain (e.g., sub.example.com → example.com)
    parts = hostname.split(".")
    if len(parts) > 2:
        hostname = ".".join(parts[-2:])

    return hostname


def compute_credibility_score(entry):
    """Compute a normalized credibility score (0–100)."""

    bias_weights = {
        "conspiracy-pseudoscience": 0.0, "conspiracy-pseuscience": 0.0,
        "questionable": 0.1, "satire": 0.2,
        "right": 0.4, "left": 0.4,
        "right-center": 0.6, "left-center": 0.6,
        "least biased": 0.9, "pro-science": 1.0,
    }
    factual_weights = {
        "very low": 0.0, "low": 0.2, "mixed": 0.4,
        "mostly factual": 0.7, "high": 0.85,
        "very high": 1.0, "n/a": 0.5,
    }
    credibility_weights = {
        "low": 0.2, "medium": 0.6,
        "high": 0.9, "high ": 0.9, "n/a": 0.5,
    }
    media_weights = {
        "government": 1.0, "journal": 0.9,
        "news agency": 0.85, "newspaper": 0.8,
        "radio station": 0.7, "tv station": 0.7,
        "organization/foundation": 0.65,
        "magazine": 0.6, "website": 0.5, "n/a": 0.5,
    }

    bias = entry.get("Bias", "N/A").strip().lower()
    factual = entry.get("Factual Reporting", "N/A").strip().lower()
    credibility = entry.get("Credibility", "N/A").strip().lower()
    media = entry.get("Media Type", "N/A").strip().lower()

    bias_score = bias_weights.get(bias, 0.5)
    factual_score = factual_weights.get(factual, 0.5)
    cred_score = credibility_weights.get(credibility, 0.5)
    media_score = media_weights.get(media, 0.5)

    final_score = (
        (bias_score * 0.3)
        + (factual_score * 0.3)
        + (cred_score * 0.3)
        + (media_score * 0.1)
    )

    return round(final_score * 100, 2)  # normalize to 0–100 scale

def check_domain(domain_or_url, json_path=CACHE_FILE):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)["data"]

    """Find a site's details by URL or domain and compute its credibility score."""
    clean_domain = extract_domain(domain_or_url)
    # print(f"\n🔍 Checking domain: {clean_domain}")

    for site in data:
        source_url = site.get("Source URL", "").lower()
        if clean_domain in source_url:
            # print("\n✅ Result Found:")
            # print(f"Source: {site.get('Source', 'N/A')}")
            # print(f"Country: {site.get('Country', 'N/A')}")
            # print(f"Media Type: {site.get('Media Type', 'N/A')}")
            # print(f"Bias: {site.get('Bias', 'N/A')}")
            # print(f"Factual Reporting: {site.get('Factual Reporting', 'N/A')}")
            # print(f"Credibility (Label): {site.get('Credibility', 'N/A')}")
            # print(f"MBFC URL: {site.get('MBFC URL', 'N/A')}")

            score = compute_credibility_score(site)
            print(f"\n⭐ Computed Credibility Score (0–1): {score}")
            return score

    print(f"\n❌ No data found for '{clean_domain}'.")
    return 0


def simulate_domain_check(retrieved_articles):
    """
    Stage 5: Real domain credibility filtering.
    - Reads MBFC dataset from mbfc_data.json
    - Extracts domain for each SERP article
    - Computes credibility score using compute_credibility_score()
    - Returns filtered credible articles for semantic matching
    """
    if not retrieved_articles:
        return {"filtered_articles": [], "avg_score": 0}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            mbfc_data = json.load(f)["data"]
    except Exception as e:
        print(f"⚠️ Could not load MBFC dataset: {e}")
        return {"filtered_articles": [], "avg_score": 0}

    results = []
    credible_articles = []

    for article in retrieved_articles:
        url = article.get("url")
        title = article.get("title", "Untitled")
        if not url:
            continue

        domain = extract_domain(url)
        found_entry = None

        for site in mbfc_data:
            source_url = site.get("Source URL", "").lower()
            if domain in source_url:
                found_entry = site
                break

        if found_entry:
            score = compute_credibility_score(found_entry)
            bias = found_entry.get("Bias", "Unknown")
            factuality = found_entry.get("Factual Reporting", "Unknown")
            credibility_label = found_entry.get("Credibility", "N/A")
        else:
            score = 50  # Neutral default
            bias, factuality, credibility_label = "Unknown", "Unknown", "N/A"

        # Map score → label
        if score >= 80:
            label = "Trusted"
        elif score >= 60:
            label = "Mostly Reliable"
        elif score >= 40:
            label = "Questionable"
        else:
            label = "Unreliable"

        results.append({
            "title": title,
            "url": url,
            "domain": domain,
            "credibility_score": score,
            "bias": bias,
            "factuality": factuality,
            "credibility_label": credibility_label,
            "label": label
        })

        # Pass only good sources (score ≥ 60) to next stage
        if score >= 60:
            credible_articles.append({"title": title, "url": url, "credibility": score})

    avg_score = round(np.mean([r["credibility_score"] for r in results]), 2)
    print(f"[INFO] Domain credibility check complete – {len(credible_articles)} credible URLs selected.")

    return {
        "avg_score": avg_score,
        "filtered_articles": credible_articles,  # [{title,url,credibility}, ...]
        "results": results
    }



# stage 5 
# ============================================================
# 🧠 STAGE 6 – SEMANTIC EMBEDDING FILTERING (Integrated)
# ============================================================

from sentence_transformers import SentenceTransformer, util

def load_or_download_model(model_name="intfloat/multilingual-e5-small", model_dir="models"):
    """
    Loads a SentenceTransformer model.
    If not present locally, downloads it once and saves it to `model_dir`.
    """
    local_model_path = os.path.join(model_dir, model_name)

    if os.path.exists(local_model_path):
        print(f"✅ Using local model: {local_model_path}")
        model = SentenceTransformer(local_model_path)
    else:
        print(f"⬇️ Model not found locally. Downloading '{model_name}' into '{local_model_path}' ...")
        os.makedirs(local_model_path, exist_ok=True)
        model = SentenceTransformer(model_name)
        model.save(local_model_path)
        print(f"✅ Model downloaded and saved at: {local_model_path}")
    
    return model


def find_similar_texts(query_text, text_list, threshold=0.9, model=None):
    """
    Compares `query_text` against each text in `text_list` using embeddings,
    and returns only those texts with cosine similarity above `threshold`.
    """
    if model is None:
        model = load_or_download_model()

    # Encode query and list of texts
    query_emb = model.encode(query_text, convert_to_tensor=True)
    list_embs = model.encode(text_list, convert_to_tensor=True)

    # Compute cosine similarities
    similarities = util.cos_sim(query_emb, list_embs)[0]

    # Collect results above threshold
    matched_texts = []
    for text, score in zip(text_list, similarities):
        sim = float(score)
        if sim >= threshold:
            matched_texts.append((text, sim))

    # Sort by similarity (descending)
    matched_texts.sort(key=lambda x: x[1], reverse=True)
    return matched_texts


def semantic_embedding(filtered_articles, claim, threshold=0.8):
    """
    Integrates semantic similarity model with domain-filtered articles.
    - Takes claim and [{title,url,credibility},...]
    - Finds articles semantically similar to claim
    - Returns top-matched URLs for Stage 7
    """
    if not filtered_articles:
        print("⚠️ No credible articles from domain check.")
        return []

    titles = [art["title"] for art in filtered_articles]
    urls = [art["url"] for art in filtered_articles]

    model = load_or_download_model()
    matches = find_similar_texts(claim, titles, threshold, model)

    if not matches:
        print("⚠️ No semantically similar headlines found.")
        return []

    selected_urls = []
    print("\n🔎 Semantic Similarity Filtering (Stage 6):")
    for title, score in matches:
        idx = titles.index(title)
        url = urls[idx]
        print(f"🟢 {score:.3f} → {title} | {url}")
        selected_urls.append(url)

    return selected_urls



# STAGE 6 – CROSS VERIFICATION & ANALYSIS
# # once all verified url is know we will run main model 

def simulate_cross_verification(claim, urls=None):
    """
    Performs scraping, summarization, and classification for verification.
    Receives:
      - claim: text of the claim
      - urls: list of verified/filtered article URLs (from Stage 5)
    Returns:
      - JSON with truthScore, final_verdict, reliable_sources, summary
    """

    # ------------------------------------------------------------
    # ⚙️ Setup
    # ------------------------------------------------------------
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    nltk.download("punkt", quiet=True)

    genai.configure(api_key= GEMINI_API)
    GEMINI_MODEL = "gemini-2.5-flash"

    # ------------------------------------------------------------
    # 🌍 Translator
    # ------------------------------------------------------------
    def translate_to_english(text: str) -> str:
        if not text or not text.strip():
            return ""
        try:
            lang = detect(text)
            if lang == "en":
                return text.strip()
            translated = GoogleTranslator(source=lang, target="en").translate(text)
            print(f"🌐 Translated from {lang} → English.")
            return translated.strip()
        except Exception as e:
            print(f"⚠️ Translation failed: {e}")
            return text.strip()

    # ------------------------------------------------------------
    # 🌐 Article extraction (multi-method)
    # ------------------------------------------------------------
    def try_newspaper(url):
        try:
            article = Article(url)
            article.download()
            article.parse()
            if len(article.text.strip()) > 50:
                return article.title, article.text.strip(), "newspaper3k"
        except Exception:
            pass
        return None

    def try_trafilatura(url):
        try:
            text = trafilatura.extract(trafilatura.fetch_url(url))
            if text and len(text.strip()) > 50:
                return "Extracted via Trafilatura", text.strip(), "trafilatura"
        except Exception:
            pass
        return None

    def extract_with_gemini(url):
        try:
            print("🔄 Gemini fallback extraction…")
            html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button", "noscript"]):
                tag.extract()
            text = soup.get_text(separator="\n", strip=True)
            if len(text) < 200:
                return None
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = f"Extract only the main article body from this text:\n{text[:2500]}"
            response = model.generate_content(prompt)
            return "Extracted via Gemini", response.text.strip(), "gemini"
        except Exception as e:
            print(f"⚠️ Gemini extraction failed: {e}")
        return None

    def extract_article(url):
        for fn in (try_newspaper, try_trafilatura, extract_with_gemini):
            result = fn(url)
            if result:
                print(f"✅ Extracted from {url} via {result[2]}")
                return {"title": result[0], "text": result[1], "method": result[2]}
        print(f"🚫 Extraction failed for: {url}")
        return None

    # ------------------------------------------------------------
    # 🧩 Models
    # ------------------------------------------------------------
    local_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    classifier = pipeline("text-classification", model="roberta-large-mnli")

    # ------------------------------------------------------------
    # 🧩 Helpers
    # ------------------------------------------------------------
    def filter_relevant_sentences(claim, text, top_k=5):
        if not text.strip():
            return ""
        claim_keywords = [w.lower() for w in claim.split() if len(w) > 3]
        sentences = nltk.sent_tokenize(text)
        relevant = [s for s in sentences if any(k in s.lower() for k in claim_keywords)]
        if len(relevant) < top_k:
            relevant = sentences[:top_k]
        return " ".join(relevant)

    def summarize_local(text):
        try:
            if len(text.split()) > 900:
                text = " ".join(text.split()[:900])
            return local_summarizer(text, max_length=200, min_length=50, do_sample=False)[0]["summary_text"].strip()
        except Exception:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            s = LexRankSummarizer()
            return " ".join(str(x) for x in s(parser.document, 3))

    def summarize_with_gemini(text):
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = f"Summarize this article in 3–5 sentences.\nInclude confirmation, denial, or verification cues.\nArticle:\n{text}"
            res = model.generate_content(prompt)
            if res and res.text:
                print("✅ Gemini summarization done.")
                return res.text.strip()
            raise Exception("Empty response")
        except Exception as e:
            print(f"⚠️ Gemini summarization failed: {e}")
            return summarize_local(text)

    def classify_claim_evidence(claim, evidence):
        result = classifier(f"Premise: {evidence} Hypothesis: {claim}", top_k=None)
        if isinstance(result, list): result = result[0]
        label = result["label"].lower()
        score = result["score"]
        if label == "entailment": meaning = True
        elif label == "contradiction": 
            meaning = False
            score = 1 - score
        else: meaning = None
        return meaning, round(score * 100, 2)

    def analyze_claim_vs_article(claim, article_text):
        claim_en = translate_to_english(claim)
        relevant = filter_relevant_sentences(claim_en, article_text)
        summary = summarize_with_gemini(relevant)

        neg = ["fake","false","denied","refuted","clarified","no such","fabricated","not true","incorrect"]
        pos = ["confirmed","agreed","verified","approved","affirmed","announced","declared"]

        if any(w in summary.lower() for w in neg):
            summary += " This indicates that the claim is false."
        elif any(w in summary.lower() for w in pos):
            summary += " This suggests the claim is true."

        relation, conf = classify_claim_evidence(claim_en, summary)
        if relation == "neutral":
            if any(w in summary.lower() for w in neg):
                print("this")
                relation, conf = False, max(90-conf, 0)
            elif any(w in summary.lower() for w in pos):
                relation, conf = True, min(conf + 10, 100)

        return {"relation": relation, "confidence": conf, "summary": summary}

    def aggregate_results(results):
        mapping = {True: 1, None: 0, False: -1}
        num = sum(mapping[r["relation"]] * r["confidence"] for r in results)
        denom = sum(r["confidence"] for r in results)
        score = num / denom if denom else 0
        truth_score = round(sum(r["confidence"] for r in results) / len(results), 2)
        if score > 0.3: final = True
        elif score < -0.3: final = False
        else: final = None
        return final, truth_score, round(score, 2)

    # ------------------------------------------------------------
    # 🧪 MAIN EXECUTION
    # ------------------------------------------------------------
    if not urls:
        print("⚠️ No URLs provided from semantic embedding. Using fallback SERP.")
        return {"truthScore": 0, "final_verdict": "UNKNOWN", "summary": "No URLs available."}

    results = []
    summaries = []
    print(f"\n🧠 CLAIM: {claim}\n{'='*80}")
    print(f"🔗 Analyzing {len(urls)} articles for verification...\n")

    for i, url in enumerate(urls, 1):
        art = extract_article(url)
        if not art:
            continue

        print(f"\n🌐 [{i}/{len(urls)}] {url}")
        print(f"📄 Title: {art['title']}")
        res = analyze_claim_vs_article(claim, art["text"])
        results.append(res)
        summaries.append(res["summary"])
        # print(f"✅ Relation: {res['relation'].upper()} ({res['confidence']}%)")

    if not results:
        print("⚠️ No valid results to aggregate.")
        return {"truthScore": 0, "final_verdict": "UNDETERMINED", "summary": "No valid extraction results."}

    final_label, truth_score, score = aggregate_results(results)

    print(f"\n📊 AGGREGATED RESULTS")
    print(f"Average confidence (TruthScore): {truth_score}%")
    print(f"🧠 FINAL VERDICT: {final_label}")

    # to see summary of each url one by one add print statement here
    # temp = simulate_domain_check(urls)
    return {
        "truthScore": truth_score,
        "final_verdict": final_label,
        "reliable_sources": [{"url": u, "name": extract_domain(u), "credibility": check_domain(u)} for u in urls],
        "summary": " ".join(summaries[:3])
    }


# ============================================================
# 🧾 STAGE 7 – COMBINE RESULTS INTO FINAL OUTPUT
# ============================================================

def combine_results(domain_result, cross_verification_result):
    """Combine all verification layers into unified output."""
    return {
        "truthScore": cross_verification_result.get("truthScore", 70),
        "verdict": cross_verification_result.get("final_verdict", "Uncertain"),
        "aiGenerated": False,
        "domain_credibility": domain_result,
        "sources": cross_verification_result.get("reliable_sources", []),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
