from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from googletrans import Translator
import re

app = Flask(__name__)

# ... all your existing functions (extract_video_id, get_transcript, etc.) ...

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    translated_summary = None
    error = None
    selected_language = "en"

    if request.method == "POST":
        url = request.form.get("youtube_url", "")
        selected_language = request.form.get("language", "en")
        video_id = extract_video_id(url)

        if not video_id:
            error = "Invalid YouTube URL."
        else:
            transcript = get_transcript(video_id)
            if transcript:
                summary = summarize_text(transcript)
                if selected_language != "en":
                    try:
                        translator = Translator()
                        translated_summary = translator.translate(summary, dest=selected_language).text
                    except Exception as e:
                        error = "Translation failed."
                        print(f"[Translation Error]: {e}")
            else:
                error = "Transcript not found."

    return render_template(
        "index.html",
        summary=summary,
        translated_summary=translated_summary,
        error=error,
        selected_language=selected_language
    )

# ⛔️ DO NOT include waitress/serve or app.run()
# Gunicorn will handle the server during deployment
