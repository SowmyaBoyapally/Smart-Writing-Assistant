from flask import Flask, render_template_string, request
from textblob import TextBlob
import language_tool_python
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import wordnet
from nltk import pos_tag
import random

# Initialize NLTK
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

app = Flask(__name__)
tool = language_tool_python.LanguageTool('en-US')

def get_synonyms(word):
    """Get synonyms for a word using WordNet"""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.name().lower() != word.lower():
                synonyms.add(lemma.name().replace('_', ' '))
    return list(synonyms)

def correct_pos(text):
    """Correct parts-of-speech errors"""
    words = word_tokenize(text)
    tagged = pos_tag(words)
    corrections = []
    
    for i, (word, tag) in enumerate(tagged):
        if i > 0 and word.lower() == 'your' and tagged[i-1][1] in ['VBZ', 'VBP']:
            corrections.append(('your', 'you'))
        elif i > 0 and word.lower() == 'are' and tagged[i-1][0].lower() == 'what':
            corrections.append(('are', 'is'))
    
    for old, new in corrections:
        text = text.replace(old, new, 1)
    return text

def analyze_text(text):
    """Analyze text with POS tagging"""
    words = word_tokenize(text)
    tagged = pos_tag(words)
    pos_freq = nltk.FreqDist(tag for (word, tag) in tagged)
    
    return {
        'words': words,
        'pos_tags': tagged,
        'pos_frequency': dict(pos_freq)
    }

def rephrase_sentence(sentence):
    """Generate alternative phrasings"""
    words = word_tokenize(sentence)
    tagged = pos_tag(words)
    rephrased = []
    
    for word, tag in tagged:
        if tag.startswith(('N', 'V', 'J', 'R')) and random.random() > 0.6:
            synonyms = get_synonyms(word)
            if synonyms:
                rephrased.append(random.choice(synonyms))
                continue
        rephrased.append(word)
    
    return ' '.join(rephrased)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize default values
    original_text = ""
    grammar_corrected = ""
    pos_corrected = ""
    analysis = {}
    rephrasings = []
    matches = []
    
    if request.method == 'POST':
        original_text = request.form['text']
        
        # Grammar correction
        matches = tool.check(original_text)
        grammar_corrected = language_tool_python.utils.correct(original_text, matches)
        
        # POS correction
        pos_corrected = correct_pos(grammar_corrected)
        
        # Text analysis
        analysis = analyze_text(pos_corrected)
        
        # Generate rephrasings
        rephrasings = [rephrase_sentence(pos_corrected) for _ in range(3)]
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Writing Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                textarea { width: 100%; height: 150px; margin-bottom: 10px; }
                button { padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                .section { margin-top: 20px; padding: 15px; border-radius: 5px; }
                .corrected { background-color: #e8f5e9; border-left: 4px solid #2e7d32; }
                .corrected-final { background-color: #f1f8e9; border-left: 4px solid #8bc34a; }
                .analysis { background-color: #e3f2fd; border-left: 4px solid #1565c0; }
                .rephrasing { background-color: #fff3e0; border-left: 4px solid #fb8c00; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <h1>Smart Writing Assistant</h1>
            <form method="POST">
                <textarea name="text" placeholder="Enter your text here...">{{ original_text }}</textarea>
                <button type="submit">Analyze</button>
            </form>
            
            {% if grammar_corrected %}
            <div class="section corrected">
                <h2>Grammar Correction</h2>
                <p><strong>Original:</strong> {{ original_text }}</p>
                <p><strong>Corrected (Grammar Only):</strong> {{ grammar_corrected }}</p>
                {% if matches %}
                    <h3>Corrections Made:</h3>
                    <ul>
                        {% for match in matches %}
                        <li>{{ match.message }} → {{ match.replacements[0] if match.replacements else 'None' }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </div>

            <div class="section corrected-final">
                <h2>Final Corrected Sentence (Grammar + POS Fixes)</h2>
                <p>{{ pos_corrected }}</p>
            </div>
            
            <div class="section analysis">
                <h2>POS Analysis</h2>
                <table>
                    <tr><th>Word</th><th>POS Tag</th></tr>
                    {% for word, tag in analysis.pos_tags %}
                    <tr><td>{{ word }}</td><td>{{ tag }}</td></tr>
                    {% endfor %}
                </table>
                <h3>POS Frequency</h3>
                <table>
                    <tr><th>POS Tag</th><th>Count</th></tr>
                    {% for tag, count in analysis.pos_frequency.items() %}
                    <tr><td>{{ tag }}</td><td>{{ count }}</td></tr>
                    {% endfor %}
                </table>
            </div>
            
            <div class="section rephrasing">
                <h2>Rephrasing Suggestions</h2>
                {% for rephrase in rephrasings %}
                <p>{{ rephrase }}</p>
                {% endfor %}
            </div>
            {% endif %}
        </body>
        </html>
    ''', original_text=original_text, grammar_corrected=grammar_corrected,
       pos_corrected=pos_corrected, analysis=analysis, rephrasings=rephrasings, matches=matches)

if __name__ == '__main__':
    app.run(debug=True)
