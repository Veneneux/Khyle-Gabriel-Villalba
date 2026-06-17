from flask import Flask, request, jsonify
from flask_cors import CORS
from newspaper import Article, ArticleException
import urllib.parse
import nltk
from datetime import datetime

# Robust NLTK setup
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('stopwords')

app = Flask(__name__)
CORS(app)

TRUSTED_OUTLETS = [
    "gmanetwork.com", "abs-cbn.com", "inquirer.net", "rappler.com", "philstar.com",
    "bbc.com", "reuters.com", "apnews.com", "nytimes.com", "cnn.com", "bloomberg.com", "abcnews.com"
]
CLICKBAIT_WORDS = ["shocking", "secret", "won't believe", "miracle cure", "conspiracy", "exposed!"]

@app.route('/verify', methods=['POST'])
def verify_link():
    data = request.get_json()
    user_url = data.get('url', '').strip()

    if not user_url:
        return jsonify({'error': 'No link provided', 'reason': 'URL input is empty.'}), 400

    parsed_url = urllib.parse.urlparse(user_url)
    domain = parsed_url.netloc.lower().replace('www.', '')

    try:
        # 1. Pipeline Execution
        scraped_article = Article(user_url)
        scraped_article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        scraped_article.config.request_timeout = 15

        scraped_article.download()
        if scraped_article.download_state != 2:
            return jsonify({"prediction": "ERROR", "reason": "Website security blocked the request.", "title": "N/A", "summary": "N/A", "keywords": [], "proof": "Blocked by WAF.", "more_info": "Connection failed."})
            
        scraped_article.parse()
        scraped_article.nlp()

        # 2. Logic Matrix Setup
        p = any(trusted in domain for trusted in TRUSTED_OUTLETS)
        text_for_scanning = (scraped_article.title + " " + scraped_article.text).lower()
        clickbait_count = sum(1 for word in CLICKBAIT_WORDS if word in text_for_scanning)
        q = clickbait_count < 2 and len(scraped_article.text) > 500
        r = p 
        
        pub_date = scraped_article.publish_date
        s = pub_date is not None
        date_str = pub_date.strftime('%Y-%m-%d') if pub_date else "Unknown"
        t = len(scraped_article.authors) > 0
        authors_list = ", ".join(scraped_article.authors) if t else "Anonymous"
        
        premise_1 = p and q and r
        premise_2 = s or t
        is_proven_real = premise_1 and premise_2

        # 3. Determine Prediction and Reason
        if is_proven_real:
            prediction = "REAL"
            reason = "The article successfully satisfies the logical conjunction properties for structural integrity."
        elif premise_1 and not premise_2:
            prediction = "UNVERIFIED"
            reason = "Source and structure hold true, but the article fails timeline accountability constraints (No date or author found)."
        else:
            prediction = "FAKE"
            reason = "The core propositional truth matrix broke down. Essential conditions for verification failed."

        proof_steps = f"Atomic Propositions: p={p}, q={q}, r={r}, s={s}, t={t}\nTheorem: (p ∧ q ∧ r) ∧ (s ∨ t)\nResult: ({int(premise_1)}) ∧ ({int(premise_2)}) ≡ {int(is_proven_real)}"
        
        # Deep-Dive metrics for the frontend
        more_info = (
            f"Domain: {domain}\n"
            f"Verified Outlet: {p}\n"
            f"Clickbait Markers Found: {clickbait_count}\n"
            f"Author(s): {authors_list}\n"
            f"Publish Date: {date_str}"
        )

        return jsonify({
            "prediction": prediction,
            "reason": reason,
            "title": scraped_article.title,
            "summary": scraped_article.summary,
            "keywords": scraped_article.keywords[:5],
            "proof": proof_steps,
            "more_info": more_info
        })

    except Exception as e:
        return jsonify({
            "prediction": "ERROR",
            "reason": f"System failure: {str(e)}",
            "title": "N/A",
            "summary": "N/A",
            "keywords": [],
            "proof": "No proof generated.",
            "more_info": "An unexpected error occurred during processing."
        })

if __name__ == '__main__':
    app.run(port=5000, debug=True)