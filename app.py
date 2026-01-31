"""
BriteCo Consumer Newsletter Generator
Flask backend API for generating monthly consumer jewelry newsletters
"""

import os
import sys
import json
import re
import base64
import secrets
from datetime import datetime
from io import BytesIO
import pytz

# Chicago timezone for timestamps
CHICAGO_TZ = pytz.timezone('America/Chicago')

from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for, Response
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

# SendGrid for email
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("[WARNING] SendGrid not installed. Email functionality disabled.")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import AI clients
from backend.integrations.openai_client import OpenAIClient
from backend.integrations.claude_client import ClaudeClient
from backend.integrations.gemini_client import GeminiClient
from backend.integrations.perplexity_client import PerplexityClient
from backend.integrations.youtube_client import get_youtube_client
from backend.integrations.blog_scraper import get_blog_scraper

# Import config
from config.consumer_brand_guidelines import (
    CONSUMER_CONTENT_TOPICS,
    CONTENT_FILTERS,
    ONTRAPORT_CONFIG,
    TEAM_MEMBERS,
    GOOGLE_DRIVE_FOLDER_ID,
    GCS_CONFIG,
    YOUTUBE_CONFIG,
    BLOG_CONFIG,
    BRAND_VOICE,
    SECTION_SPECS,
    WRITING_STYLE_GUIDE,
    BRAND_CHECK_RULES,
    EMAIL_TEMPLATE_CONFIG,
    AI_PROMPTS,
    MONTH_TO_SEASON,
    EDITORIAL_STYLE_GUIDE,
)
from config.model_config import get_model_for_task

# Initialize Flask app
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Fix for running behind Cloud Run's proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Session configuration for OAuth
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

ALLOWED_DOMAIN = 'brite.co'

def get_current_user():
    """Get current authenticated user from session"""
    return session.get('user')

# Initialize AI clients
openai_client = None
claude_client = None
gemini_client = None
perplexity_client = None

try:
    openai_client = OpenAIClient()
    print("[OK] OpenAI initialized")
except Exception as e:
    print(f"[WARNING] OpenAI not available: {e}")

try:
    gemini_client = GeminiClient()
    if gemini_client.is_available():
        print("[OK] Gemini initialized")
    else:
        print("[WARNING] Gemini not available - add GOOGLE_AI_API_KEY")
except Exception as e:
    print(f"[WARNING] Gemini not available: {e}")

try:
    claude_client = ClaudeClient()
    print("[OK] Claude initialized")
except Exception as e:
    print(f"[WARNING] Claude not available: {e}")

try:
    perplexity_client = PerplexityClient()
    print("[OK] Perplexity initialized")
except Exception as e:
    print(f"[WARNING] Perplexity not available: {e}")

# Initialize YouTube and Blog clients
youtube_client = get_youtube_client()
blog_scraper = get_blog_scraper()

# Google Cloud Storage
GCS_DRAFTS_BUCKET = GCS_CONFIG['drafts_bucket']
GCS_IMAGES_BUCKET = GCS_CONFIG['images_bucket']
gcs_client = None
try:
    from google.cloud import storage as gcs_storage
    gcs_client = gcs_storage.Client()
    print("[OK] GCS initialized")
except Exception as e:
    print(f"[WARNING] GCS not available: {e}")

# Safe print for Unicode
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


# ============================================================================
# OAUTH AUTHENTICATION ROUTES
# ============================================================================

@app.route('/auth/login')
def auth_login():
    """Redirect to Google OAuth"""
    if get_current_user():
        return redirect('/')
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Google"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            return 'Failed to get user info', 400

        email = user_info.get('email', '')

        if not email.endswith(f'@{ALLOWED_DOMAIN}'):
            return f'''
            <html>
            <head><title>Access Denied</title></head>
            <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #272D3F;">
                <div style="text-align: center; color: white; padding: 2rem;">
                    <h1 style="color: #FC883A;">Access Denied</h1>
                    <p>Only @{ALLOWED_DOMAIN} email addresses are allowed.</p>
                    <p style="color: #A9C1CB;">You tried to sign in with: {email}</p>
                    <a href="/auth/login" style="color: #31D7CA;">Try again with a different account</a>
                </div>
            </body>
            </html>
            ''', 403

        session['user'] = {
            'email': email,
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', '')
        }

        return redirect('/')

    except Exception as e:
        print(f"[AUTH ERROR] OAuth callback failed: {e}")
        return f'Authentication failed: {str(e)}', 500


@app.route('/auth/logout')
def auth_logout():
    """Clear session and redirect to login"""
    session.pop('user', None)
    return redirect('/auth/login')


# ============================================================================
# ROUTES - STATIC FILES
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the main app with auth check"""
    user = get_current_user()
    if not user:
        return redirect('/auth/login')

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    user_script = f'''<script>
    window.AUTH_USER = {json.dumps(user)};
    </script>
</head>'''
    html = html.replace('</head>', user_script, 1)

    return Response(html, mimetype='text/html')

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "app": "BriteCo Consumer Newsletter", "timestamp": datetime.now().isoformat()})


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_domain(url):
    """Extract domain name from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return 'Unknown'


def convert_markdown_to_html(text):
    """Convert markdown formatting to HTML"""
    if not text:
        return text
    text = str(text)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" style="color: #008181; text-decoration: underline;">\1</a>',
        text
    )
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text


def process_generated_content(content):
    """Process generated content to convert markdown to HTML"""
    if isinstance(content, dict):
        return {k: process_generated_content(v) for k, v in content.items()}
    elif isinstance(content, list):
        return [process_generated_content(item) for item in content]
    elif isinstance(content, str):
        return convert_markdown_to_html(content)
    return content


def html_to_plain_text(html_content):
    """Convert HTML to plain text for email"""
    if not html_content:
        return ''
    text = str(html_content)
    text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', r'\2 (\1)', text)
    text = re.sub(r'<li[^>]*>', '- ', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_json_from_llm(content):
    """Extract JSON from LLM response that may contain markdown code blocks"""
    if not content:
        return {}
    content = content.strip()
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    return json.loads(content)


def resize_image(base64_data, target_size):
    """Resize image to target dimensions"""
    try:
        from PIL import Image, ImageOps
        image_bytes = base64.b64decode(base64_data)
        pil_image = Image.open(BytesIO(image_bytes))
        resized = ImageOps.fit(pil_image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        buffer = BytesIO()
        resized.save(buffer, format='PNG', optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        safe_print(f"  Resize error: {e}")
        return base64_data


# ============================================================================
# ROUTES - YOUTUBE VIDEOS
# ============================================================================

@app.route('/api/youtube/videos', methods=['GET'])
def get_youtube_videos():
    """Get BriteCo YouTube channel videos"""
    try:
        sort = request.args.get('sort', 'popular')
        max_results = int(request.args.get('max_results', '20'))

        if not youtube_client.is_available():
            return jsonify({'success': False, 'error': 'YouTube API key not configured'}), 503

        videos = youtube_client.get_videos_sorted(
            sort=sort,
            channel_id=YOUTUBE_CONFIG['channel_id'],
            max_results=max_results
        )

        return jsonify({'success': True, 'videos': videos})

    except Exception as e:
        safe_print(f"[API ERROR] YouTube videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/youtube/video-by-url', methods=['POST'])
def get_youtube_video_by_url():
    """Get video details from a YouTube URL"""
    try:
        url = request.json.get('url', '')
        if not url:
            return jsonify({'success': False, 'error': 'URL required'}), 400

        if not youtube_client.is_available():
            return jsonify({'success': False, 'error': 'YouTube API key not configured'}), 503

        video = youtube_client.get_video_by_url(url)
        if video:
            return jsonify({'success': True, 'video': video})
        else:
            return jsonify({'success': False, 'error': 'Video not found'}), 404

    except Exception as e:
        safe_print(f"[API ERROR] YouTube video by URL: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - BLOG POSTS
# ============================================================================

@app.route('/api/blog/posts', methods=['GET'])
def get_blog_posts():
    """Get recent BriteCo blog posts"""
    try:
        count = int(request.args.get('count', '10'))
        category = request.args.get('category', None)
        search = request.args.get('search', None)

        posts = blog_scraper.get_recent_posts(
            count=count,
            category=category,
            search=search
        )

        return jsonify({'success': True, 'posts': posts})

    except Exception as e:
        safe_print(f"[API ERROR] Blog posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/blog/categories', methods=['GET'])
def get_blog_categories():
    """Get blog categories"""
    try:
        categories = blog_scraper.get_categories()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - GUESS THE PRICE
# ============================================================================

@app.route('/api/guess-the-price/search', methods=['POST'])
def gtp_search():
    """Search for Guess the Price items via Perplexity"""
    try:
        data = request.json
        query = data.get('query', 'rare expensive jewelry 2026')
        time_window = data.get('time_window', '30d')

        if not perplexity_client or not perplexity_client.is_available():
            return jsonify({'success': False, 'error': 'Perplexity API not configured'}), 503

        search_query = f"""Find notable, expensive, or famous jewelry pieces: {query}

Focus on:
- Celebrity-owned jewelry
- Auction records and rare pieces
- Famous diamonds, gems, and collections
- High-value jewelry in the news
- Pieces with interesting backstories

Include specific details about materials, provenance, and estimated values when available."""

        results = perplexity_client.search(
            query=search_query,
            time_window=time_window,
            max_results=6
        )

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        safe_print(f"[API ERROR] GTP search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/guess-the-price/generate-details', methods=['POST'])
def gtp_generate_details():
    """Generate Guess the Price details using Claude"""
    try:
        data = request.json
        title = data.get('title', '')
        url = data.get('url', '')
        snippet = data.get('snippet', '')

        if not claude_client:
            return jsonify({'success': False, 'error': 'Claude not available'}), 503

        prompt = AI_PROMPTS['generate_guess_the_price_details'].format(
            title=title,
            url=url,
            snippet=snippet
        )

        response = claude_client.generate_content(
            prompt=prompt,
            max_tokens=400,
            temperature=0.5
        )

        details = parse_json_from_llm(response.get('content', '{}'))

        return jsonify({'success': True, 'details': details})

    except Exception as e:
        safe_print(f"[API ERROR] GTP generate details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - QUICK TIP GENERATION
# ============================================================================

@app.route('/api/generate-quick-tip', methods=['POST'])
def generate_quick_tip():
    """Generate a seasonal quick tip"""
    try:
        data = request.json
        month = data.get('month', datetime.now().strftime('%B')).lower()
        season = MONTH_TO_SEASON.get(month, 'winter')

        themes = SECTION_SPECS['quick_tip']['seasonal_themes'].get(month, ['jewelry care tips'])
        themes_str = ', '.join(themes)

        if not claude_client:
            return jsonify({'success': False, 'error': 'Claude not available'}), 503

        prompt = AI_PROMPTS['generate_quick_tip'].format(
            month=month.title(),
            season=season,
            themes=themes_str
        )

        response = claude_client.generate_content(
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )

        tip_text = response.get('content', '').strip()

        # Generate an image prompt for the tip
        image_prompt = f"Photorealistic jewelry care photography, {season} setting, elegant flat lay with jewelry cleaning supplies and fine jewelry, soft natural lighting, stock photo quality, {themes[0] if themes else 'jewelry care'}"

        return jsonify({
            'success': True,
            'tip': tip_text,
            'image_prompt': image_prompt
        })

    except Exception as e:
        safe_print(f"[API ERROR] Generate quick tip: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - CONTENT GENERATION
# ============================================================================

@app.route('/api/rewrite-content', methods=['POST'])
def rewrite_content():
    """AI rewrite for consumer newsletter sections"""
    try:
        data = request.json
        content = data.get('content', '')
        tone = data.get('tone', 'friendly')
        section = data.get('section', 'general')

        if not claude_client:
            return jsonify({'success': False, 'error': 'Claude not available'}), 503

        tone_map = {
            'friendly': 'Friendly and warm, like texting a knowledgeable friend',
            'witty': 'Witty and clever, with wordplay and pop culture references',
            'informative': 'Informative but engaging, clear and accessible',
            'playful': 'Playful and fun, light-hearted with personality',
            'professional': 'Professional but approachable, polished yet warm'
        }

        word_limits = {
            'intro': 40,
            'video_description': 80,
            'quick_tip': 60,
            'guess_the_price_question': 30,
        }

        max_words = word_limits.get(section, 100)

        prompt = f"""Rewrite this content for a consumer jewelry newsletter.

Section: {section}
Tone: {tone_map.get(tone, tone)}
Max words: {max_words}

Original content:
{content}

Guidelines:
- Consumer-friendly language (not B2B)
- Engaging, conversational tone
- Max {max_words} words
- Follow BriteCo editorial style (serial commas, em dashes with no spaces, lab-grown hyphenated)

Return ONLY the rewritten text, nothing else."""

        response = claude_client.generate_content(
            prompt=prompt,
            max_tokens=300,
            temperature=0.7
        )

        rewritten = response.get('content', content).strip()

        return jsonify({
            'success': True,
            'rewritten': rewritten,
            'tone': tone,
            'section': section
        })

    except Exception as e:
        safe_print(f"[API ERROR] Rewrite: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-newsletter', methods=['POST'])
def generate_newsletter():
    """Generate consumer newsletter content using Claude"""
    try:
        data = request.json
        month = data.get('month', '')
        intro = data.get('intro', '')
        news_of_month = data.get('news_of_month', {})
        trend_alert = data.get('trend_alert', {})
        blog_articles = data.get('blog_articles', [])
        guess_the_price = data.get('guess_the_price', {})
        quick_tip = data.get('quick_tip', '')

        safe_print(f"\n[API] Generating consumer newsletter for {month}...")

        generated = {}

        # 1. Generate intro if not provided
        if intro:
            generated['intro'] = intro
        else:
            highlights = []
            if news_of_month.get('title'):
                highlights.append(f"News of Month: {news_of_month['title']}")
            if trend_alert.get('title'):
                highlights.append(f"Trend Alert: {trend_alert['title']}")
            if guess_the_price.get('title'):
                highlights.append(f"Guess the Price: {guess_the_price['title']}")

            try:
                prompt = AI_PROMPTS['generate_intro'].format(
                    month=month,
                    highlights='; '.join(highlights) if highlights else 'jewelry news and trends'
                )
                response = claude_client.generate_content(prompt=prompt, max_tokens=150, temperature=0.8)
                generated['intro'] = response.get('content', '').strip()
            except Exception as e:
                safe_print(f"  Error generating intro: {e}")
                generated['intro'] = f"Welcome to the {month} edition of BriteCo's newsletter!"

        # 2. Generate What's Inside agenda
        try:
            sections_to_tease = []
            if news_of_month.get('title'):
                sections_to_tease.append(f"News of Month video: {news_of_month['title']}")
            if trend_alert.get('title'):
                sections_to_tease.append(f"Trend Alert video: {trend_alert['title']}")
            if blog_articles:
                titles = [a.get('title', '') for a in blog_articles[:2]]
                sections_to_tease.append(f"Blog articles: {', '.join(titles)}")
            if guess_the_price.get('title'):
                sections_to_tease.append(f"Guess the Price: {guess_the_price['title']}")

            prompt = AI_PROMPTS['generate_whats_inside'].format(
                sections='\n'.join(f"- {s}" for s in sections_to_tease)
            )
            response = claude_client.generate_content(prompt=prompt, max_tokens=300, temperature=0.8)
            content = response.get('content', '')

            # Parse bullet items from response
            items = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    line = line.lstrip('-* ').strip()
                if line and len(line) > 5:
                    items.append(line)
            generated['agenda_items'] = items[:4]

        except Exception as e:
            safe_print(f"  Error generating agenda: {e}")
            generated['agenda_items'] = [
                f"The latest jewelry news from BriteCo",
                f"A trend you need to know about",
                f"Two must-read blog articles",
                f"Can you guess the price of this famous piece?"
            ]

        # 3. Generate News of Month description
        if news_of_month.get('title'):
            try:
                prompt = AI_PROMPTS['generate_video_description'].format(
                    max_words=80,
                    title=news_of_month.get('title', ''),
                    description=news_of_month.get('description', '')[:500]
                )
                response = claude_client.generate_content(prompt=prompt, max_tokens=200, temperature=0.6)
                generated['news_of_month'] = {
                    'title': news_of_month.get('title', ''),
                    'description': response.get('content', '').strip(),
                    'thumbnail_url': news_of_month.get('thumbnail_url', ''),
                    'video_url': news_of_month.get('url', '')
                }
            except Exception as e:
                safe_print(f"  Error generating news_of_month desc: {e}")
                generated['news_of_month'] = {
                    'title': news_of_month.get('title', ''),
                    'description': news_of_month.get('description', '')[:200],
                    'thumbnail_url': news_of_month.get('thumbnail_url', ''),
                    'video_url': news_of_month.get('url', '')
                }

        # 4. Generate Trend Alert description
        if trend_alert.get('title'):
            try:
                prompt = AI_PROMPTS['generate_video_description'].format(
                    max_words=80,
                    title=trend_alert.get('title', ''),
                    description=trend_alert.get('description', '')[:500]
                )
                response = claude_client.generate_content(prompt=prompt, max_tokens=200, temperature=0.6)
                generated['trend_alert'] = {
                    'title': trend_alert.get('title', ''),
                    'description': response.get('content', '').strip(),
                    'thumbnail_url': trend_alert.get('thumbnail_url', ''),
                    'video_url': trend_alert.get('url', '')
                }
            except Exception as e:
                safe_print(f"  Error generating trend_alert desc: {e}")
                generated['trend_alert'] = {
                    'title': trend_alert.get('title', ''),
                    'description': trend_alert.get('description', '')[:200],
                    'thumbnail_url': trend_alert.get('thumbnail_url', ''),
                    'video_url': trend_alert.get('url', '')
                }

        # 5. Blog articles (pass through - titles/images come from the blog)
        generated['blog_articles'] = []
        for article in blog_articles[:2]:
            generated['blog_articles'].append({
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'featured_image_url': article.get('featured_image_url', ''),
                'excerpt': article.get('excerpt', '')
            })

        # 6. Guess the Price question text
        if guess_the_price.get('title'):
            try:
                prompt = f"""Write a teasing question for a "Guess the Price" section about this jewelry piece.

Item: {guess_the_price.get('title', '')}
Material: {guess_the_price.get('material', '')}
Fun Fact: {guess_the_price.get('fun_fact', '')}

Write ONE short, teasing question (max 15 words) that builds suspense about the price.
Examples: "Think you know what this rare gem is worth?", "Can you guess the price tag on this iconic piece?"

Return ONLY the question text."""

                response = claude_client.generate_content(prompt=prompt, max_tokens=60, temperature=0.7)
                gtp_question = response.get('content', 'Think you know the price?').strip().strip('"')
            except:
                gtp_question = "Think you know the price?"

            generated['guess_the_price'] = {
                'title': guess_the_price.get('title', ''),
                'image_url': guess_the_price.get('image_url', ''),
                'material': guess_the_price.get('material', ''),
                'found_in': guess_the_price.get('found_in', ''),
                'where_it_lives': guess_the_price.get('where_it_lives', ''),
                'fun_fact': guess_the_price.get('fun_fact', ''),
                'question': gtp_question,
                'link': guess_the_price.get('source_link', guess_the_price.get('url', '#'))
            }

        # 7. Quick tip
        if quick_tip:
            generated['quick_tip'] = quick_tip
        else:
            # Auto-generate if not provided
            season = MONTH_TO_SEASON.get(month.lower(), 'winter')
            themes = SECTION_SPECS['quick_tip']['seasonal_themes'].get(month.lower(), ['jewelry care'])
            try:
                prompt = AI_PROMPTS['generate_quick_tip'].format(
                    month=month,
                    season=season,
                    themes=', '.join(themes)
                )
                response = claude_client.generate_content(prompt=prompt, max_tokens=200, temperature=0.7)
                generated['quick_tip'] = response.get('content', '').strip()
            except:
                generated['quick_tip'] = f"Keep your jewelry sparkling this {season}!"

        # Convert markdown links to HTML
        generated = process_generated_content(generated)

        return jsonify({
            'success': True,
            'generated': generated,
            'month': month
        })

    except Exception as e:
        safe_print(f"[API ERROR] Generate newsletter: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - BRAND CHECK
# ============================================================================

@app.route('/api/check-brand-guidelines', methods=['POST'])
def check_brand_guidelines():
    """Check content against consumer brand guidelines"""
    try:
        data = request.json
        content = data.get('content', {})
        month = data.get('month', '')

        safe_print(f"\n[API] Checking brand guidelines for {month}...")

        content_text = json.dumps(content, indent=2)[:4000]

        prompt = AI_PROMPTS['brand_check'].format(content=content_text)

        response = claude_client.generate_content(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3
        )

        result = parse_json_from_llm(response.get('content', '{}'))

        return jsonify({
            'success': True,
            'brand_check': result
        })

    except Exception as e:
        safe_print(f"[API ERROR] Brand check: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - IMAGE GENERATION
# ============================================================================

@app.route('/api/generate-image-prompts', methods=['POST'])
def generate_image_prompts():
    """Generate image prompts for consumer newsletter sections"""
    try:
        data = request.json
        sections = data.get('sections', {})

        safe_print(f"\n[API] Generating image prompts for {len(sections)} sections...")

        prompts = {}

        for section, content in sections.items():
            if not content:
                continue

            safe_print(f"  - Creating image prompt for {section}")

            title = content.get('title', content.get('tip', ''))
            body = content.get('content', content.get('description', content.get('tip', '')))
            if isinstance(body, dict):
                body = body.get('description', '') or body.get('content', '') or str(body)
            body = str(body) if body else ''

            prompt_request = f"""Create a text-to-image prompt for a consumer jewelry newsletter image.

Section: {section}
Title: "{title}"
Content: "{body[:400]}..."

Requirements:
- Photorealistic, professional photography style
- Stock photo aesthetic - luxury jewelry photography
- Elegant lighting, warm tones, aspirational feel
- Teal/gold color accents where appropriate (BriteCo brand)
- No text overlays in the image
- Clean, well-lit, high-quality imagery
- Consumer-facing aesthetic (not B2B)

Output ONLY the image generation prompt, nothing else."""

            try:
                response = claude_client.generate_content(
                    prompt=prompt_request,
                    max_tokens=150,
                    temperature=0.5
                )
                prompts[section] = {
                    'prompt': response.get('content', '').strip(),
                    'title': title
                }
            except Exception as e:
                safe_print(f"  Error generating prompt for {section}: {e}")
                prompts[section] = {
                    'prompt': f"Photorealistic luxury jewelry photography, elegant display, soft warm lighting, {title}, high-end aesthetic",
                    'title': title
                }

        return jsonify({'success': True, 'prompts': prompts})

    except Exception as e:
        safe_print(f"[API ERROR] Image prompts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-images', methods=['POST'])
def generate_images():
    """Generate images using Gemini"""
    try:
        data = request.json
        prompts = data.get('prompts', {})

        safe_print(f"\n[API] Generating {len(prompts)} images...")

        if not gemini_client or not gemini_client.is_available():
            return jsonify({'success': False, 'error': 'Gemini image generation not available'}), 500

        images = {}

        IMAGE_SIZES = {
            'quick_tip': (490, 300),
            'guess_the_price': (250, 250),
        }

        ASPECT_RATIOS = {
            'quick_tip': '16:9',
            'guess_the_price': '1:1',
        }

        for section, prompt_data in prompts.items():
            prompt = prompt_data.get('prompt', '')
            if not prompt:
                continue

            safe_print(f"  Generating image for {section}...")

            try:
                aspect_ratio = ASPECT_RATIOS.get(section, '1:1')
                result = gemini_client.generate_image(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio
                )

                image_data = result.get('image_data', '')

                if image_data:
                    target_size = IMAGE_SIZES.get(section, (300, 300))
                    image_data = resize_image(image_data, target_size)

                images[section] = {
                    'url': f"data:image/png;base64,{image_data}" if image_data else '',
                    'prompt': prompt
                }

            except Exception as e:
                safe_print(f"  Error generating image for {section}: {e}")
                images[section] = {'url': '', 'prompt': prompt, 'error': str(e)}

        return jsonify({'success': True, 'images': images})

    except Exception as e:
        safe_print(f"[API ERROR] Generate images: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-single-image', methods=['POST'])
def generate_single_image():
    """Generate a single image using Gemini"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        section = data.get('section', 'generic')

        if not prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400

        if not gemini_client or not gemini_client.is_available():
            return jsonify({'success': False, 'error': 'Gemini not available'}), 500

        IMAGE_SIZES = {
            'quick_tip': (490, 300),
            'guess_the_price': (250, 250),
        }
        ASPECT_RATIOS = {
            'quick_tip': '16:9',
            'guess_the_price': '1:1',
        }

        aspect_ratio = ASPECT_RATIOS.get(section, '1:1')
        result = gemini_client.generate_image(prompt=prompt, aspect_ratio=aspect_ratio)
        image_data = result.get('image_data', '')

        if image_data:
            target_size = IMAGE_SIZES.get(section, (300, 300))
            image_data = resize_image(image_data, target_size)

        return jsonify({
            'success': True,
            'image_url': f"data:image/png;base64,{image_data}" if image_data else ''
        })

    except Exception as e:
        safe_print(f"[API ERROR] Generate single image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/resize-image', methods=['POST'])
def resize_image_endpoint():
    """Resize an image to specified dimensions"""
    try:
        data = request.json
        image_url = data.get('image_url', '')
        width = data.get('width', 300)
        height = data.get('height', 300)
        section = data.get('section', 'generic')

        if not image_url:
            return jsonify({'success': False, 'error': 'No image URL provided'}), 400

        if image_url.startswith('data:'):
            base64_data = image_url.split(',')[1] if ',' in image_url else ''
        else:
            import requests as req
            response = req.get(image_url)
            base64_data = base64.b64encode(response.content).decode('utf-8')

        if not base64_data:
            return jsonify({'success': False, 'error': 'Could not extract image data'}), 400

        resized_data = resize_image(base64_data, (width, height))
        return jsonify({
            'success': True,
            'resized_url': f"data:image/png;base64,{resized_data}"
        })

    except Exception as e:
        safe_print(f"[API ERROR] Resize image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - SUBJECT LINES
# ============================================================================

@app.route('/api/generate-subject-lines', methods=['POST'])
def generate_subject_lines():
    """Generate subject line and preheader options for consumer newsletter"""
    try:
        data = request.json
        content = data.get('content', {})
        month = data.get('month', '')
        year = data.get('year', datetime.now().year)
        tone = data.get('tone', 'playful')

        safe_print(f"\n[API] Generating subject lines for {month}, tone: {tone}...")

        highlights = []
        if content.get('news_of_month', {}).get('title'):
            highlights.append(f"Video: {content['news_of_month']['title']}")
        if content.get('guess_the_price', {}).get('title'):
            highlights.append(f"Guess the Price: {content['guess_the_price']['title']}")
        if content.get('quick_tip'):
            highlights.append("Quick jewelry tip")

        prompt = AI_PROMPTS['generate_subject_lines'].format(
            month=month,
            year=year,
            highlights='; '.join(highlights) if highlights else 'jewelry trends and tips'
        )

        response = claude_client.generate_content(
            prompt=prompt,
            max_tokens=500,
            temperature=0.8
        )

        options = parse_json_from_llm(response.get('content', '{}'))

        return jsonify({
            'success': True,
            'subject_lines': options.get('subject_lines', options) if isinstance(options, dict) else options,
            'preheaders': options.get('preheaders', []) if isinstance(options, dict) else []
        })

    except Exception as e:
        safe_print(f"[API ERROR] Subject lines: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - EXPORT & EMAIL
# ============================================================================

@app.route('/api/send-preview', methods=['POST'])
def send_preview():
    """Send copy review email to team via SendGrid"""
    try:
        data = request.json
        recipients = data.get('recipients', [])
        subject = data.get('subject', 'BriteCo Consumer Newsletter - Copy Review')
        html_content = data.get('html', '')

        if not recipients or not html_content:
            return jsonify({"success": False, "error": "Recipients and HTML content required"}), 400

        safe_print(f"[API] Sending copy review to {len(recipients)} recipients via SendGrid...")

        if not SENDGRID_AVAILABLE:
            return jsonify({"success": False, "error": "SendGrid library not installed"}), 500

        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY') or os.environ.get('_SENDGRID_API_KEY')
        from_email = os.environ.get('SENDGRID_FROM_EMAIL') or ONTRAPORT_CONFIG['from_email']
        from_name = os.environ.get('SENDGRID_FROM_NAME') or ONTRAPORT_CONFIG['from_name']

        if not sendgrid_api_key:
            return jsonify({"success": False, "error": "SendGrid API key not configured"}), 500

        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)

        sent_count = 0
        errors = []

        for recipient in recipients:
            try:
                message = Mail(
                    from_email=(from_email, from_name),
                    to_emails=recipient,
                    subject=subject,
                    html_content=html_content
                )
                response = sg.send(message)
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                else:
                    errors.append(f"Failed for {recipient}: status {response.status_code}")
            except Exception as email_error:
                errors.append(f"Failed for {recipient}: {str(email_error)}")

        return jsonify({
            "success": sent_count > 0,
            "message": f"Copy review sent to {sent_count} recipient(s)",
            "errors": errors if errors else None
        })

    except Exception as e:
        safe_print(f"[API] Send preview error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/export-to-docs', methods=['POST'])
def export_to_docs():
    """Export consumer newsletter content to Google Docs"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        data = request.json
        content = data.get('content', {})
        month = data.get('month', datetime.now().strftime('%B'))
        year = data.get('year', datetime.now().year)
        title = data.get('title', f"{year} {month} - Consumer Newsletter")
        send_email = data.get('send_email', False)
        recipients = data.get('recipients', [])

        safe_print(f"[API] Exporting to Google Docs: {title}")

        creds_json = os.environ.get('GOOGLE_DOCS_CREDENTIALS') or os.environ.get('_GOOGLE_DOCS_CREDENTIALS')

        if not creds_json:
            return jsonify({"success": False, "error": "Google Docs credentials not configured."}), 500

        try:
            creds_data = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
            )
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid Google credentials: {str(e)}"}), 500

        docs_service = build('docs', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }

        created_file = drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()

        doc_id = created_file.get('id')
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        # Build document content
        requests_list = []
        index_offset = [1]

        def add_text(text, bold=False, heading=False, link_url=None):
            if not text:
                return
            text = str(text).strip() + '\n\n'
            start_index = index_offset[0]
            end_index = start_index + len(text)

            requests_list.append({
                'insertText': {'location': {'index': start_index}, 'text': text}
            })

            if heading:
                requests_list.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': start_index, 'endIndex': end_index - 1},
                        'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                        'fields': 'namedStyleType'
                    }
                })
            elif bold:
                requests_list.append({
                    'updateTextStyle': {
                        'range': {'startIndex': start_index, 'endIndex': end_index - 1},
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })

            if link_url:
                requests_list.append({
                    'updateTextStyle': {
                        'range': {'startIndex': start_index, 'endIndex': end_index - 2},
                        'textStyle': {
                            'link': {'url': link_url},
                            'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.51, 'blue': 0.51}}}
                        },
                        'fields': 'link,foregroundColor'
                    }
                })

            index_offset[0] = end_index

        # Add content sections
        add_text(title, heading=True)

        # Introduction
        if content.get('intro'):
            add_text('Introduction', bold=True)
            add_text(content['intro'])

        # What's Inside
        if content.get('agenda_items'):
            add_text("What's Inside", bold=True)
            items = content['agenda_items']
            if isinstance(items, list):
                for item in items:
                    add_text(f"- {item}")
            else:
                add_text(str(items))

        # News of the Month
        nom = content.get('news_of_month', {})
        if isinstance(nom, dict) and nom.get('title'):
            add_text('News of the Month', bold=True)
            add_text(nom.get('title', ''))
            add_text(nom.get('description', ''))
            if nom.get('video_url'):
                add_text(f"Video: {nom['video_url']}", link_url=nom['video_url'])

        # Trend Alert
        ta = content.get('trend_alert', {})
        if isinstance(ta, dict) and ta.get('title'):
            add_text('Trend Alert', bold=True)
            add_text(ta.get('title', ''))
            add_text(ta.get('description', ''))
            if ta.get('video_url'):
                add_text(f"Video: {ta['video_url']}", link_url=ta['video_url'])

        # Blog Articles
        blogs = content.get('blog_articles', [])
        if blogs:
            add_text('Blog Articles', bold=True)
            for i, blog in enumerate(blogs[:2], 1):
                if isinstance(blog, dict):
                    add_text(f"Article {i}: {blog.get('title', '')}", link_url=blog.get('url'))
                else:
                    add_text(f"Article {i}: {str(blog)}")

        # Guess the Price
        gtp = content.get('guess_the_price', {})
        if isinstance(gtp, dict) and gtp.get('title'):
            add_text('Guess the Price', bold=True)
            add_text(gtp.get('title', ''))
            add_text(f"Material: {gtp.get('material', '')}")
            add_text(f"Found In: {gtp.get('found_in', '')}")
            add_text(f"Where It Lives: {gtp.get('where_it_lives', '')}")
            add_text(f"Fun Fact: {gtp.get('fun_fact', '')}")
            add_text(f"Question: {gtp.get('question', '')}")
            if gtp.get('link'):
                add_text(f"Source: {gtp['link']}", link_url=gtp['link'])

        # Quick Tip
        if content.get('quick_tip'):
            add_text('Quick Tip', bold=True)
            add_text(content['quick_tip'])

        # Execute batch update
        if requests_list:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests_list}
            ).execute()

        # Make accessible
        drive_service.permissions().create(
            fileId=doc_id,
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True
        ).execute()

        # Send copy review email if requested
        emails_sent = []
        if send_email and recipients and SENDGRID_AVAILABLE:
            sendgrid_api_key = os.environ.get('SENDGRID_API_KEY') or os.environ.get('_SENDGRID_API_KEY')
            from_email = os.environ.get('SENDGRID_FROM_EMAIL') or ONTRAPORT_CONFIG['from_email']
            from_name = os.environ.get('SENDGRID_FROM_NAME') or ONTRAPORT_CONFIG['from_name']

            if sendgrid_api_key:
                sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)

                for recipient in recipients:
                    try:
                        email_html = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #008181;">Consumer Newsletter - Ready for Review</h2>
                            <p>The <strong>{month} {year}</strong> consumer newsletter has been exported to Google Docs for copy review.</p>
                            <p style="margin: 20px 0;">
                                <a href="{doc_url}" style="background: #008181; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                                    Open Google Doc
                                </a>
                            </p>
                        </div>
                        """

                        message = Mail(
                            from_email=(from_email, from_name),
                            to_emails=recipient,
                            subject=f"Consumer Newsletter - {month} {year} - Copy Review",
                            html_content=email_html
                        )
                        response = sg.send(message)
                        if response.status_code in [200, 201, 202]:
                            emails_sent.append(recipient)
                    except Exception as email_error:
                        safe_print(f"[API] Email error for {recipient}: {email_error}")

        return jsonify({
            "success": True,
            "doc_url": doc_url,
            "doc_id": doc_id,
            "title": title,
            "emails_sent": emails_sent
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/send-doc-notification', methods=['POST'])
def send_doc_notification():
    """Send email notification with Google Doc link"""
    try:
        data = request.json
        recipients = data.get('recipients', [])
        doc_url = data.get('doc_url', '')
        month = data.get('month', '')
        year = data.get('year', datetime.now().year)

        if not recipients or not doc_url:
            return jsonify({"success": False, "error": "Recipients and doc_url required"}), 400

        if not SENDGRID_AVAILABLE:
            return jsonify({"success": False, "error": "SendGrid not available"}), 500

        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY') or os.environ.get('_SENDGRID_API_KEY')
        from_email = os.environ.get('SENDGRID_FROM_EMAIL') or ONTRAPORT_CONFIG['from_email']
        from_name = os.environ.get('SENDGRID_FROM_NAME') or ONTRAPORT_CONFIG['from_name']

        if not sendgrid_api_key:
            return jsonify({"success": False, "error": "SendGrid API key not configured"}), 500

        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        sent = []

        for recipient in recipients:
            try:
                email_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #008181;">Consumer Newsletter - Copy Review</h2>
                    <p>The <strong>{month} {year}</strong> consumer newsletter is ready for review.</p>
                    <p style="margin: 20px 0;">
                        <a href="{doc_url}" style="background: #008181; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                            Open Google Doc
                        </a>
                    </p>
                </div>
                """

                message = Mail(
                    from_email=(from_email, from_name),
                    to_emails=recipient,
                    subject=f"Consumer Newsletter - {month} {year} - Copy Review",
                    html_content=email_html
                )
                response = sg.send(message)
                if response.status_code in [200, 201, 202]:
                    sent.append(recipient)
            except Exception as email_error:
                safe_print(f"[API] Notification error for {recipient}: {email_error}")

        return jsonify({
            "success": len(sent) > 0,
            "emails_sent": sent
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# ROUTES - FETCH ARTICLE METADATA
# ============================================================================

@app.route('/api/fetch-article-metadata', methods=['POST'])
def fetch_article_metadata():
    """Fetch metadata from a URL (used for Guess the Price link uploads)"""
    try:
        import requests as req
        from bs4 import BeautifulSoup

        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = req.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except req.RequestException as e:
            return jsonify({'success': False, 'error': f'Failed to fetch URL: {str(e)}'}), 400

        soup = BeautifulSoup(response.text, 'html.parser')

        title = ''
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']
        elif soup.title:
            title = soup.title.string or ''

        description = ''
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            description = og_desc['content']
        else:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content']

        image = ''
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image = og_image['content']

        publisher = extract_domain(url)
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            publisher = og_site['content']

        published_date = ''
        article_date = soup.find('meta', property='article:published_time')
        if article_date and article_date.get('content'):
            published_date = article_date['content']

        return jsonify({
            'success': True,
            'metadata': {
                'title': title.strip() if title else 'Untitled',
                'description': description.strip()[:500] if description else '',
                'image': image,
                'publisher': publisher,
                'published_date': published_date,
                'url': url
            }
        })

    except Exception as e:
        safe_print(f"[API ERROR] Fetch metadata: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - ONTRAPORT
# ============================================================================

@app.route('/api/push-to-ontraport', methods=['POST'])
def push_to_ontraport():
    """Push consumer newsletter to Ontraport"""
    try:
        import requests as req

        data = request.json
        subject = data.get('subject')
        month = data.get('month', 'Newsletter')
        html_content = data.get('html')

        if not subject or not html_content:
            return jsonify({'success': False, 'error': 'Missing subject or HTML content'}), 400

        safe_print(f"\n[ONTRAPORT] Pushing consumer newsletter to Ontraport...")

        ontraport_app_id = os.getenv('ONTRAPORT_APP_ID', '').strip()
        ontraport_api_key = os.getenv('ONTRAPORT_API_KEY', '').strip()

        if not ontraport_app_id or not ontraport_api_key:
            return jsonify({'success': False, 'error': 'Ontraport credentials not configured.'}), 400

        headers = {
            'Api-Appid': ontraport_app_id,
            'Api-Key': ontraport_api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        plain_text = html_to_plain_text(html_content)

        payload = {
            'objectID': ONTRAPORT_CONFIG['object_id'],
            'name': f'BriteCo Consumer Newsletter {month.title()}',
            'subject': subject,
            'type': 'e-mail',
            'transactional_email': '0',
            'object_type_id': ONTRAPORT_CONFIG['object_type_id'],
            'from': 'custom',
            'send_out_name': ONTRAPORT_CONFIG['from_name'],
            'reply_to_email': ONTRAPORT_CONFIG['reply_to_email'],
            'send_from': ONTRAPORT_CONFIG['from_email'],
            'send_to': 'email',
            'message_body': html_content,
            'text_body': plain_text
        }

        response = req.post(
            'https://api.ontraport.com/1/message',
            headers=headers,
            data=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            safe_print(f"[ONTRAPORT] Success!")
            return jsonify({'success': True, 'message': 'Newsletter pushed to Ontraport', 'data': result})
        else:
            error_msg = f"Ontraport API error: {response.status_code} - {response.text}"
            safe_print(f"[ONTRAPORT ERROR] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500

    except Exception as e:
        safe_print(f"[API ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - EMAIL TEMPLATE RENDERING
# ============================================================================

@app.route('/api/render-email-template', methods=['POST'])
def render_email_template():
    """Render consumer email template with newsletter content"""
    try:
        data = request.json
        content = data.get('content', {})
        month = data.get('month', datetime.now().strftime('%B'))
        year = data.get('year', datetime.now().year)
        preheader = data.get('preheader', f"Your monthly jewelry inspiration from BriteCo - {month} {year}")
        images = data.get('images', {})

        safe_print(f"\n[API] Rendering consumer email template for {month} {year}...")

        template_path = os.path.join('templates', 'consumer-newsletter-email.html')
        if not os.path.exists(template_path):
            return jsonify({'success': False, 'error': 'Email template not found'}), 404

        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Basic placeholders
        html = html.replace('{{MONTH}}', month)
        html = html.replace('{{YEAR}}', str(year))
        html = html.replace('{{PREHEADER}}', preheader)

        # Intro
        html = html.replace('{{INTRO_TEXT}}', content.get('intro', f'Welcome to the {month} edition!'))

        # What's Inside agenda
        agenda_items = content.get('agenda_items', [])
        agenda_html = ''
        for item in agenda_items[:4]:
            item_text = item if isinstance(item, str) else str(item)
            agenda_html += f'''<tr>
<td style="padding-bottom: 10px;">
<p style="margin: 0; font-family: 'Wix Madefor Display', Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; font-weight: 400; color: #282e40;">{item_text}</p>
</td>
</tr>'''
        html = html.replace('{{AGENDA_ITEMS}}', agenda_html)

        # News of the Month
        nom = content.get('news_of_month', {})
        if isinstance(nom, dict):
            html = html.replace('{{NEWS_MONTH_TITLE}}', nom.get('title', 'News of the Month'))
            html = html.replace('{{NEWS_MONTH_THUMBNAIL}}', nom.get('thumbnail_url', ''))
            html = html.replace('{{NEWS_MONTH_DESCRIPTION}}', nom.get('description', ''))
            html = html.replace('{{NEWS_MONTH_VIDEO_URL}}', nom.get('video_url', '#'))
        else:
            html = html.replace('{{NEWS_MONTH_TITLE}}', 'News of the Month')
            html = html.replace('{{NEWS_MONTH_THUMBNAIL}}', '')
            html = html.replace('{{NEWS_MONTH_DESCRIPTION}}', '')
            html = html.replace('{{NEWS_MONTH_VIDEO_URL}}', '#')

        # Trend Alert
        ta = content.get('trend_alert', {})
        if isinstance(ta, dict):
            html = html.replace('{{TREND_TITLE}}', ta.get('title', 'Trend Alert'))
            html = html.replace('{{TREND_THUMBNAIL}}', ta.get('thumbnail_url', ''))
            html = html.replace('{{TREND_DESCRIPTION}}', ta.get('description', ''))
            html = html.replace('{{TREND_VIDEO_URL}}', ta.get('video_url', '#'))
        else:
            html = html.replace('{{TREND_TITLE}}', 'Trend Alert')
            html = html.replace('{{TREND_THUMBNAIL}}', '')
            html = html.replace('{{TREND_DESCRIPTION}}', '')
            html = html.replace('{{TREND_VIDEO_URL}}', '#')

        # Blog Articles
        blogs = content.get('blog_articles', [{}, {}])
        blog_1 = blogs[0] if len(blogs) > 0 else {}
        blog_2 = blogs[1] if len(blogs) > 1 else {}

        html = html.replace('{{BLOG_1_TITLE}}', blog_1.get('title', 'Blog Article'))
        html = html.replace('{{BLOG_1_IMAGE}}', blog_1.get('featured_image_url', ''))
        html = html.replace('{{BLOG_1_URL}}', blog_1.get('url', '#'))

        html = html.replace('{{BLOG_2_TITLE}}', blog_2.get('title', 'Blog Article'))
        html = html.replace('{{BLOG_2_IMAGE}}', blog_2.get('featured_image_url', ''))
        html = html.replace('{{BLOG_2_URL}}', blog_2.get('url', '#'))

        # Guess the Price
        gtp = content.get('guess_the_price', {})
        if isinstance(gtp, dict):
            html = html.replace('{{GTP_TITLE}}', gtp.get('title', 'Guess the Price'))
            gtp_image = gtp.get('image_url', '')
            if images.get('guess_the_price', {}).get('url'):
                gtp_image = images['guess_the_price']['url']
            html = html.replace('{{GTP_IMAGE}}', gtp_image)
            html = html.replace('{{GTP_MATERIAL}}', gtp.get('material', ''))
            html = html.replace('{{GTP_FOUND_IN}}', gtp.get('found_in', ''))
            html = html.replace('{{GTP_WHERE_IT_LIVES}}', gtp.get('where_it_lives', ''))
            html = html.replace('{{GTP_FUN_FACT}}', gtp.get('fun_fact', ''))
            html = html.replace('{{GTP_QUESTION}}', gtp.get('question', 'Think you know the price?'))
            html = html.replace('{{GTP_LINK}}', gtp.get('link', '#'))
        else:
            for placeholder in ['GTP_TITLE', 'GTP_IMAGE', 'GTP_MATERIAL', 'GTP_FOUND_IN',
                                'GTP_WHERE_IT_LIVES', 'GTP_FUN_FACT', 'GTP_QUESTION', 'GTP_LINK']:
                html = html.replace('{{' + placeholder + '}}', '')

        # Quick Tip
        html = html.replace('{{QUICK_TIP_TEXT}}', content.get('quick_tip', ''))

        # Quick tip image block
        quick_tip_image = images.get('quick_tip', {}).get('url', '')
        if quick_tip_image:
            quick_tip_image_html = f'''
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 20px;">
<tr>
<td>
<img src="{quick_tip_image}" width="590" alt="Quick Tip" style="width: 100%; max-width: 590px; height: auto; display: block; border-radius: 6px;" class="mobile-img-full">
</td>
</tr>
</table>'''
        else:
            quick_tip_image_html = ''
        html = html.replace('{{QUICK_TIP_IMAGE_BLOCK}}', quick_tip_image_html)

        return jsonify({
            'success': True,
            'html': html,
            'month': month,
            'year': year
        })

    except Exception as e:
        safe_print(f"[API ERROR] Render template: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - DRAFTS (Google Cloud Storage)
# ============================================================================

SAVED_ITEMS_BLOB = 'saved-items/global.json'

@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Auto-save newsletter draft to GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        data = request.json
        month = data.get('month', 'unknown').lower()
        year = data.get('year', datetime.now().year)
        saved_by = data.get('savedBy', 'unknown').split('@')[0].replace('.', '-')
        blob_name = f"drafts/{month}-{year}-{saved_by}.json"

        draft = {
            'month': month,
            'year': year,
            'newsletterType': 'consumer',
            'currentStep': data.get('currentStep'),
            'selectedContent': data.get('selectedContent'),
            'generatedContent': data.get('generatedContent'),
            'generatedImages': data.get('generatedImages'),
            'generatedPrompts': data.get('generatedPrompts'),
            'introText': data.get('introText'),
            'quickTipText': data.get('quickTipText'),
            'subjectLine': data.get('subjectLine'),
            'preheader': data.get('preheader'),
            'lastSavedBy': data.get('savedBy', 'unknown'),
            'lastSavedAt': datetime.now(CHICAGO_TZ).isoformat()
        }

        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(draft), content_type='application/json')
        return jsonify({'success': True, 'file': blob_name})

    except Exception as e:
        safe_print(f"[DRAFT SAVE ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list-drafts', methods=['GET'])
def list_drafts():
    """List all saved drafts from GCS"""
    if not gcs_client:
        return jsonify({'success': True, 'drafts': []})
    try:
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blobs = bucket.list_blobs(prefix='drafts/')
        drafts = []
        for blob in blobs:
            if not blob.name.endswith('.json'):
                continue
            data = json.loads(blob.download_as_text())
            drafts.append({
                'month': data.get('month'),
                'year': data.get('year'),
                'currentStep': data.get('currentStep'),
                'lastSavedBy': data.get('lastSavedBy'),
                'lastSavedAt': data.get('lastSavedAt'),
                'filename': blob.name
            })
        drafts.sort(key=lambda d: d.get('lastSavedAt', ''), reverse=True)
        return jsonify({'success': True, 'drafts': drafts})
    except Exception as e:
        safe_print(f"[DRAFT LIST ERROR] {str(e)}")
        return jsonify({'success': True, 'drafts': []})


@app.route('/api/load-draft', methods=['GET'])
def load_draft():
    """Load a specific draft from GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(filename)
        data = json.loads(blob.download_as_text())
        return jsonify({'success': True, 'draft': data})
    except Exception as e:
        safe_print(f"[DRAFT LOAD ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publish-draft', methods=['POST'])
def publish_draft():
    """Move draft to published in GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        filename = request.json.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        source_blob = bucket.blob(filename)
        if not source_blob.exists():
            return jsonify({'success': False, 'error': 'Draft not found'}), 404
        published_name = filename.replace('drafts/', 'published/', 1)
        bucket.copy_blob(source_blob, bucket, published_name)
        source_blob.delete()
        safe_print(f"[DRAFT] Published {filename} -> {published_name}")
        return jsonify({'success': True, 'file': published_name})
    except Exception as e:
        safe_print(f"[DRAFT PUBLISH ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list-published', methods=['GET'])
def list_published():
    """List all published newsletters from GCS"""
    if not gcs_client:
        return jsonify({'success': True, 'newsletters': []})
    try:
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blobs = list(bucket.list_blobs(prefix='published/'))
        newsletters = []
        for blob in blobs:
            if blob.name.endswith('.json'):
                data = json.loads(blob.download_as_text())
                gc = data.get('generatedContent', {})
                newsletters.append({
                    'filename': blob.name,
                    'month': data.get('month'),
                    'year': data.get('year'),
                    'lastSavedBy': data.get('lastSavedBy'),
                    'lastSavedAt': data.get('lastSavedAt'),
                })
        newsletters.sort(key=lambda d: d.get('lastSavedAt', ''), reverse=True)
        return jsonify({'success': True, 'newsletters': newsletters})
    except Exception as e:
        safe_print(f"[PUBLISHED LIST ERROR] {str(e)}")
        return jsonify({'success': True, 'newsletters': []})


@app.route('/api/load-published', methods=['GET'])
def load_published():
    """Load a specific published newsletter from GCS"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(filename)
        if not blob.exists():
            return jsonify({'success': False, 'error': 'Not found'}), 404
        data = json.loads(blob.download_as_text())
        return jsonify({'success': True, 'draft': data})
    except Exception as e:
        safe_print(f"[PUBLISHED LOAD ERROR] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-draft', methods=['DELETE'])
def delete_draft():
    """Delete a draft from GCS"""
    if not gcs_client:
        return jsonify({'success': True})
    try:
        filename = request.json.get('file')
        if not filename:
            return jsonify({'success': False, 'error': 'No file specified'}), 400
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(filename)
        if blob.exists():
            blob.delete()
        return jsonify({'success': True})
    except Exception as e:
        safe_print(f"[DRAFT DELETE ERROR] {str(e)}")
        return jsonify({'success': True})


# ============================================================================
# ROUTES - SAVED ITEMS (for Guess the Price)
# ============================================================================

@app.route('/api/saved-articles', methods=['GET'])
def get_saved_articles():
    """Get saved items from GCS"""
    if not gcs_client:
        return jsonify({'success': True, 'articles': []})
    try:
        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(SAVED_ITEMS_BLOB)
        if blob.exists():
            data = json.loads(blob.download_as_text())
            return jsonify({'success': True, 'articles': data.get('articles', [])})
        return jsonify({'success': True, 'articles': []})
    except Exception as e:
        safe_print(f"[SAVED ITEMS] Error loading: {str(e)}")
        return jsonify({'success': True, 'articles': []})


@app.route('/api/saved-articles', methods=['POST'])
def add_saved_article():
    """Add item to saved list"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        article = request.json.get('article')
        if not article or not article.get('url'):
            return jsonify({'success': False, 'error': 'Article with URL required'}), 400

        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(SAVED_ITEMS_BLOB)

        articles = []
        if blob.exists():
            data = json.loads(blob.download_as_text())
            articles = data.get('articles', [])

        if any(a.get('url') == article['url'] for a in articles):
            return jsonify({'success': True, 'message': 'Already saved', 'articles': articles})

        article['dateSaved'] = datetime.now(CHICAGO_TZ).isoformat()
        articles.insert(0, article)

        blob.upload_from_string(json.dumps({'articles': articles}), content_type='application/json')
        return jsonify({'success': True, 'articles': articles})

    except Exception as e:
        safe_print(f"[SAVED ITEMS] Error saving: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/saved-articles', methods=['DELETE'])
def delete_saved_article():
    """Remove item from saved list by URL"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not available'}), 503
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'URL required'}), 400

        bucket = gcs_client.bucket(GCS_DRAFTS_BUCKET)
        blob = bucket.blob(SAVED_ITEMS_BLOB)

        articles = []
        if blob.exists():
            data = json.loads(blob.download_as_text())
            articles = data.get('articles', [])

        articles = [a for a in articles if a.get('url') != url]
        blob.upload_from_string(json.dumps({'articles': articles}), content_type='application/json')
        return jsonify({'success': True, 'articles': articles})

    except Exception as e:
        safe_print(f"[SAVED ITEMS] Error deleting: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - IMAGE HOSTING (GCS)
# ============================================================================

@app.route('/api/upload-images-to-gcs', methods=['POST'])
def upload_images_to_gcs():
    """Upload newsletter images to GCS and return public URLs"""
    if not gcs_client:
        return jsonify({'success': False, 'error': 'GCS not configured'}), 500

    try:
        data = request.json
        images_data = data.get('images', {})
        month = data.get('month', 'unknown')
        year = data.get('year', datetime.now().year)

        if not images_data:
            return jsonify({'success': False, 'error': 'No images provided'}), 400

        bucket = gcs_client.bucket(GCS_IMAGES_BUCKET)
        uploaded_urls = {}
        timestamp = datetime.now(CHICAGO_TZ).strftime('%Y%m%d-%H%M%S')

        for section, data_url in images_data.items():
            if not data_url or not data_url.startswith('data:image'):
                continue

            try:
                header, b64_data = data_url.split(',', 1)
                img_format = 'png'
                if 'jpeg' in header or 'jpg' in header:
                    img_format = 'jpg'
                elif 'webp' in header:
                    img_format = 'webp'

                image_bytes = base64.b64decode(b64_data)

                safe_section = section.replace('_', '-')
                filename = f"newsletters/{year}/{month.lower()}/{timestamp}-{safe_section}.{img_format}"

                blob = bucket.blob(filename)
                blob.upload_from_string(image_bytes, content_type=f'image/{img_format}')
                blob.make_public()

                uploaded_urls[section] = blob.public_url
                safe_print(f"[GCS] Uploaded {section} -> {blob.public_url}")

            except Exception as img_error:
                safe_print(f"[GCS] Error uploading {section}: {str(img_error)}")
                continue

        return jsonify({
            'success': True,
            'urls': uploaded_urls,
            'count': len(uploaded_urls)
        })

    except Exception as e:
        safe_print(f"[GCS UPLOAD] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - PERPLEXITY SEARCH (general)
# ============================================================================

@app.route('/api/v2/search-perplexity', methods=['POST'])
def search_perplexity():
    """Search via Perplexity API (general consumer jewelry search)"""
    try:
        data = request.json
        query = data.get('query', '')
        time_window = data.get('time_window', '30d')

        if not query:
            return jsonify({'success': False, 'error': 'Query required'}), 400

        if not perplexity_client or not perplexity_client.is_available():
            return jsonify({'success': False, 'error': 'Perplexity not configured'}), 503

        results = perplexity_client.search(
            query=query,
            time_window=time_window,
            max_results=6
        )

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        safe_print(f"[API ERROR] Perplexity search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print(f"\n{'='*60}")
    print(f"  BriteCo Consumer Newsletter Generator")
    print(f"  Running on http://localhost:{port}")
    print(f"{'='*60}\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
