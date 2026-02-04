"""
BriteCo Consumer Newsletter Configuration
Brand guidelines, editorial style rules, and newsletter settings for consumer audience.
"""

# ─────────────────────────────────────────────
# Content Topics & Filters
# ─────────────────────────────────────────────

CONSUMER_CONTENT_TOPICS = [
    "engagement rings",
    "wedding jewelry",
    "jewelry care",
    "jewelry trends",
    "celebrity jewelry",
    "jewelry fashion",
    "fine jewelry",
    "diamonds",
    "gemstones",
    "luxury watches",
    "jewelry appraisal",
    "jewelry insurance",
    "lab-grown diamonds",
    "vintage jewelry",
    "estate jewelry",
    "custom jewelry",
    "jewelry styling",
    "birthstones",
    "precious metals",
    "gold prices",
    "rare gems",
    "jewelry collecting",
]

CONTENT_FILTERS = {
    "include": [
        "jewelry",
        "engagement rings",
        "wedding bands",
        "diamonds",
        "gemstones",
        "jewelry care",
        "jewelry trends",
        "celebrity jewelry",
        "jewelry fashion",
        "fine jewelry",
        "luxury watches",
        "jewelry appraisal",
        "jewelry insurance",
        "lab-grown diamonds",
        "vintage jewelry",
        "rare gems",
        "jewelry collecting",
        "precious metals",
        "gold prices",
    ],
    "exclude": [
        "B2B",
        "jeweler business",
        "trade show",
        "wholesale",
        "political",
        "election",
        "obituary",
        "passed away",
        "death",
        "promoted to",
        "new CEO",
    ],
}


# ─────────────────────────────────────────────
# Ontraport Configuration
# ─────────────────────────────────────────────

ONTRAPORT_CONFIG = {
    "object_id": "7",
    "object_type_id": "10000",
    "from_email": "insurance@brite.co",
    "reply_to_email": "insurance@brite.co",
    "from_name": "BriteCo Insurance",
}


# ─────────────────────────────────────────────
# Team Members (SendGrid copy review recipients)
# ─────────────────────────────────────────────

TEAM_MEMBERS = [
    {"name": "Dylanne Crugnale", "email": "dylanne.crugnale@brite.co"},
    {"name": "Selena Fragassi", "email": "selena.fragassi@brite.co"},
]


# ─────────────────────────────────────────────
# Google Drive & GCS
# ─────────────────────────────────────────────

GOOGLE_DRIVE_FOLDER_ID = "1HafFd1vuelwaHFDlH-fS1dpTIucAGmdg"

GCS_CONFIG = {
    "drafts_bucket": "consumer-drafts",
    "images_bucket": "consumer-images",
    "drafts_prefix": "drafts/",
    "published_prefix": "published/",
}


# ─────────────────────────────────────────────
# YouTube Configuration
# ─────────────────────────────────────────────

YOUTUBE_CONFIG = {
    "channel_id": "UCrPdDfZ6Sk6H3GqzTCpsyyQ",
    "channel_name": "BriteCo",
    "default_sort": "popular",
    "max_results": 20,
}


# ─────────────────────────────────────────────
# Blog Configuration
# ─────────────────────────────────────────────

BLOG_CONFIG = {
    "url": "https://brite.co/blog/",
    "wp_api_base": "https://brite.co/wp-json/wp/v2",
    "default_count": 10,
}


# ─────────────────────────────────────────────
# Brand Voice
# ─────────────────────────────────────────────

BRAND_VOICE = {
    "tone": (
        "Friendly, engaging, and fun. Like a knowledgeable friend who happens "
        "to know everything about jewelry. Relatable and approachable — never "
        "stuffy or overly formal. Light humor and pop culture references welcome."
    ),
    "style": (
        "Conversational and warm with personality. Short punchy sentences mixed "
        "with flowing descriptions. Use vivid imagery and relatable comparisons."
    ),
    "perspective": (
        "We help jewelry lovers protect and celebrate their most treasured pieces. "
        "We're the friend who's always up on the latest jewelry trends."
    ),
    "audience": (
        "Consumer jewelry owners and enthusiasts — engaged couples, collectors, "
        "fashion-forward individuals, gift-givers, and anyone who loves beautiful "
        "jewelry. Not industry professionals."
    ),
    "wit_guidance": [
        "Witty one-liners and wordplay are encouraged, especially in the intro",
        "Pop culture references and timely hooks are great openers",
        "Keep humor relatable — think fun newsletter friend, not stand-up comic",
        "Emojis are welcome in What's Inside bullet items",
        "Never sacrifice clarity for cleverness",
        "Puns on jewelry/gem terms are on-brand",
    ],
    "avoid": [
        "B2B or industry-insider jargon",
        "Overly salesy or pushy language",
        "Condescending 'educating the consumer' tone",
        "Political content",
        "Forced or cringeworthy humor",
        "Personnel/people news",
        "Technical insurance jargon (keep CTA simple and friendly)",
    ],
}


# ─────────────────────────────────────────────
# Editorial Style Guide
# ─────────────────────────────────────────────

EDITORIAL_STYLE_GUIDE = {
    "numbers": {
        "rule": "Spell out one through nine; use numerals for 10 and above",
        "exceptions": [
            "Always use numerals with % (5%, not five percent)",
            "Always use numerals for prices ($5, $1,200)",
            "Always use numerals for ages (5 years old)",
            "Spell out at start of sentence (Twelve percent...)",
        ],
    },
    "percentages": {
        "rule": "Use the % symbol, not 'percent'",
        "examples": ["5%", "not 'five percent'", "not '5 percent'"],
    },
    "punctuation": {
        "serial_comma": "Always use the serial/Oxford comma",
        "em_dash": "Use em dashes (—) with no spaces on either side",
        "ellipsis": "Use three periods with no spaces (...)",
        "exclamation": "Use sparingly — max one per paragraph",
        "examples": [
            "diamonds, emeralds, and sapphires (serial comma)",
            "The ring—a stunning 3-carat diamond—was appraised at $50,000 (em dash)",
        ],
    },
    "capitalization": {
        "rule": "Use title case for section headers and article titles",
        "title_case_rules": [
            "Capitalize first and last word always",
            "Capitalize nouns, verbs, adjectives, adverbs, pronouns",
            "Lowercase articles (a, an, the) unless first/last",
            "Lowercase prepositions (in, on, at, for, to, with) unless first/last",
            "Lowercase conjunctions (and, but, or, nor) unless first/last",
        ],
    },
    "abbreviations": {
        "rule": "Spell out on first reference, abbreviate thereafter",
        "always_abbreviated": ["U.S.", "GIA", "AGS", "?"
                               "CEO", "DIY"],
        "note": "Do not assume reader knows industry abbreviations",
    },
    "hyphenation": {
        "rules": [
            "lab-grown (always hyphenated)",
            "well-known, high-end, long-term (hyphenate compound adjectives before nouns)",
            "Do not hyphenate after adverbs ending in -ly (newly designed ring)",
        ],
    },
    "brand_names": {
        "BriteCo": {
            "correct": "BriteCo",
            "incorrect": ["Briteco", "briteco", "BRITECO", "Brite Co", "Brite.co"],
            "note": "Capital B, capital C, one word, no space",
        },
        "general_rule": "Always verify correct spelling and capitalization of brand names",
    },
    "inclusive_language": {
        "rules": [
            "Use 'partner' or 'spouse' rather than assuming gender",
            "Use 'they/their' as singular when gender is unknown",
            "Avoid gendered assumptions about jewelry purchases",
            "Use 'person' or 'people' instead of gendered terms where possible",
        ],
    },
    "briteco_dos_and_donts": {
        "do": [
            "Refer to BriteCo as a jewelry insurance provider",
            "Emphasize ease and convenience of coverage",
            "Mention appraisal and protection together",
            "Use friendly, approachable language about insurance",
        ],
        "dont": [
            "Never position BriteCo as a traditional insurance company",
            "Never use fear-based selling language",
            "Never make guarantees about claims or coverage",
            "Never compare negatively to other insurance providers",
        ],
    },
}


# ─────────────────────────────────────────────
# Consumer Newsletter Sections (7 sections)
# ─────────────────────────────────────────────

SECTION_SPECS = {
    "intro": {
        "description": "Fun, witty opening that hooks the reader and sets the tone",
        "format": "1-2 sentences, italic, conversational",
        "max_words": 40,
        "style_notes": [
            "Start with a pop culture reference, seasonal hook, or witty observation",
            "Tie the hook to jewelry/the newsletter content",
            "Should feel like a clever friend texting you",
        ],
        "example_openers": [
            "This holiday season, take a page out of Liz Taylor's book—or jewelry box, rather—and treat yourself to something that sparkles as much as you do.",
            "PSL's may be over, but sparkle season is just getting started.",
            "From Louvre drama to PSL-worthy sparkle, this month is serving looks—and we're here for all of them.",
            "New year, new satisfying piece of ice—who needs resolutions when you've got carats?",
        ],
    },
    "whats_inside": {
        "description": "Bulleted agenda previewing the newsletter sections",
        "format": "4 bullet items with emojis",
        "style_notes": [
            "Each bullet is a teaser for a section below",
            "Use relevant emojis at the start of each bullet",
            "Keep each bullet to one short, catchy line",
            "Build curiosity — don't give everything away",
        ],
        "example_items": [
            "💍 The viral video jewelers don't want you to see",
            "🔥 Lab-grown vs. natural: the trend that's dividing the industry",
            "📖 Two must-read guides for protecting your bling",
            "💎 Can you guess the price of this high-profile rock?",
            "✨ A quick tip to keep your sparkle game strong all winter",
            "🐾 How to include pets in your big day (yes, really)",
        ],
    },
    "news_of_month": {
        "description": "Featured BriteCo YouTube video with description",
        "content_source": "YouTube Data API v3",
        "format": "Video thumbnail + 3-4 sentence description",
        "max_words": 80,
        "requires_video": True,
        "cta_text": "Watch the full video here",
        "style_notes": [
            "Summarize the video content in consumer-friendly language",
            "Highlight the most interesting/useful takeaway",
            "End with a hook that encourages watching the full video",
            "White text on dark background — keep sentences short and scannable",
        ],
    },
    "trend_alert": {
        "description": "Second BriteCo YouTube video highlighting a trend",
        "content_source": "YouTube Data API v3",
        "format": "Video thumbnail + 3-4 sentence description",
        "max_words": 80,
        "requires_video": True,
        "cta_text": "Watch the full video here",
        "style_notes": [
            "Focus on what's trending and why readers should care",
            "Use language that creates urgency or FOMO",
            "Connect the trend to the reader's life/style",
            "Same styling and format as News of the Month",
        ],
    },
    "blog_articles": {
        "description": "Two BriteCo blog article cards side by side",
        "content_source": "brite.co/blog WordPress REST API",
        "format": "2 cards with featured image + title + READ MORE button",
        "articles_count": 2,
        "requires_image": True,
        "cta_text": "READ MORE",
        "style_notes": [
            "Use the blog post's existing title (may lightly edit for length)",
            "Featured image from the blog post",
            "Cards should be visually balanced — similar image sizes",
        ],
    },
    "guess_the_price": {
        "description": "Interactive section showcasing a notable jewelry piece",
        "content_source": "Perplexity search + manual link + Claude AI details",
        "format": "Image left + 4 detail fields right + price question",
        "detail_fields": {
            "material": {
                "label": "Material",
                "description": "Primary materials (e.g., '18K White Gold, 3.5ct Oval Diamond')",
                "max_words": 15,
            },
            "found_in": {
                "label": "Found In",
                "description": "Where it was discovered or context (e.g., 'Christie's Spring Auction 2026')",
                "max_words": 15,
            },
            "where_it_lives": {
                "label": "Where It Lives",
                "description": "Current home or owner type (e.g., 'Private collection, New York')",
                "max_words": 15,
            },
            "fun_fact": {
                "label": "Fun Fact",
                "description": "Interesting trivia about the piece (e.g., 'Once owned by a Hollywood starlet')",
                "max_words": 20,
            },
        },
        "question_format": "Think you know the price? Click here to find out!",
        "style_notes": [
            "Choose items with visual wow-factor and interesting backstories",
            "Details should be intriguing and conversation-worthy",
            "Fun Fact should make the reader want to share with friends",
            "Celebrity, auction, or record-breaking items work great",
            "The title often names the specific piece (e.g., 'The Blue Moon Diamond')",
        ],
        "example_titles": [
            "The Pink Star Diamond",
            "Elizabeth Taylor's Bulgari Emerald Suite",
            "A high-profile, celebrity-owned rare sapphire ring",
        ],
    },
    "quick_tip": {
        "description": "Seasonal jewelry care or styling tip",
        "format": "1-2 short paragraphs with teal bullet icon, optional image below",
        "max_words": 60,
        "requires_image": False,
        "style_notes": [
            "Practical, actionable advice the reader can use immediately",
            "Tie to the current season or upcoming events",
            "Friendly, helpful tone — like advice from a knowledgeable friend",
            "Keep it concise — this is a quick tip, not an article",
        ],
        "seasonal_themes": {
            "january": ["New Year jewelry care reset", "winter storage tips", "post-holiday cleaning"],
            "february": ["Valentine's Day gift care", "engagement ring maintenance", "winter skin and jewelry"],
            "march": ["spring cleaning for jewelry", "switching seasonal pieces", "preparing for spring events"],
            "april": ["spring event jewelry", "rain and jewelry care", "gemstone spotlight"],
            "may": ["wedding season prep", "Mother's Day jewelry care", "outdoor event tips"],
            "june": ["summer jewelry care", "beach and pool safety", "wedding jewelry tips"],
            "july": ["travel with jewelry", "heat and humidity protection", "summer styling"],
            "august": ["back-to-school jewelry", "late summer care", "jewelry organization"],
            "september": ["fall transition pieces", "Labor Day to layering", "appraisal season reminder"],
            "october": ["fall jewelry trends", "costume vs. fine jewelry", "Halloween sparkle"],
            "november": ["holiday shopping prep", "Black Friday jewelry tips", "gift guide insights"],
            "december": ["holiday party jewelry", "year-end appraisals", "winter protection tips"],
        },
    },
    "insurance_cta": {
        "description": "Static insurance call-to-action section",
        "format": "Heading + subtext + CTA button",
        "heading": "Cover Your Sparkle",
        "subtext": "BriteCo offers affordable, comprehensive jewelry insurance that's easy to set up and gives you peace of mind.",
        "cta_text": "GET A FREE QUOTE",
        "cta_url": "https://brite.co/jewelry-insurance/",
        "style_notes": [
            "This section is static — same content every issue",
            "Do not use fear-based language",
            "Keep it friendly and inviting",
        ],
    },
}


# ─────────────────────────────────────────────
# Writing Style Guide (Consumer Voice)
# ─────────────────────────────────────────────

WRITING_STYLE_GUIDE = {
    "intro": {
        "patterns": [
            "Open with a pop culture hook, seasonal reference, or witty one-liner",
            "Tie the hook back to jewelry or the newsletter content",
            "Use italic styling for the intro text",
            "Keep it to 1-2 punchy sentences (max 40 words)",
        ],
        "tone": "Witty, warm, conversational — like a fun friend's text message",
    },
    "whats_inside": {
        "patterns": [
            "4 bullet items with leading emojis",
            "Each bullet teases a section without giving it all away",
            "Use action words and curiosity-building phrases",
            "Keep each bullet to one line",
        ],
    },
    "video_descriptions": {
        "patterns": [
            "Summarize the video's key takeaway in 3-4 sentences",
            "Use consumer-friendly language — no jargon",
            "End with a hook that encourages clicking through",
            "Max 80 words per description",
        ],
        "applies_to": ["news_of_month", "trend_alert"],
        "tone": "Informative but engaging — make the reader curious",
    },
    "guess_the_price": {
        "patterns": [
            "Title names the specific piece or gives a teasing description",
            "Detail fields are concise and intriguing",
            "Fun Fact should be shareable/conversation-worthy",
            "Question text builds suspense and encourages the click",
        ],
        "tone": "Playful and intriguing — like a fun quiz",
    },
    "quick_tip": {
        "patterns": [
            "Lead with the actionable advice",
            "Tie to season or current events",
            "1-2 short paragraphs, max 60 words total",
            "Practical and immediately useful",
        ],
        "tone": "Helpful friend giving quick advice",
    },
}


# ─────────────────────────────────────────────
# Brand Check Rules
# ─────────────────────────────────────────────

BRAND_CHECK_RULES = {
    "tone_and_voice": {
        "should_be": (
            "Friendly, fun, engaging, and relatable. Like a knowledgeable "
            "friend sharing jewelry news over coffee."
        ),
        "should_avoid": (
            "B2B jargon, insurance-speak, condescending tone, "
            "overly formal language, fear-based selling, forced humor."
        ),
    },
    "word_count_limits": {
        "intro": 40,
        "news_of_month_description": 80,
        "trend_alert_description": 80,
        "quick_tip": 60,
        "guess_the_price_detail_field": 20,
    },
    "required_elements": {
        "intro": ["witty_opener"],
        "whats_inside": ["4_bullet_items", "emojis"],
        "news_of_month": ["video_thumbnail", "description", "video_link"],
        "trend_alert": ["video_thumbnail", "description", "video_link"],
        "blog_articles": ["2_articles", "featured_images", "read_more_links"],
        "guess_the_price": ["image", "material", "found_in", "where_it_lives", "fun_fact", "question_link"],
        "quick_tip": ["tip_text"],
        "insurance_cta": ["heading", "cta_button"],
    },
    "editorial_checks": [
        "BriteCo spelled correctly (capital B, capital C, one word)",
        "Serial/Oxford comma used consistently",
        "Em dashes with no spaces (—)",
        "Numbers: spell out 1-9, numerals for 10+",
        "Percentages use % symbol",
        "Lab-grown is hyphenated",
        "Title case on section headers",
        "Inclusive language (partner/spouse, singular they)",
        "No fear-based insurance language",
        "No B2B or industry jargon",
    ],
    "content_filters": {
        "exclude_topics": [
            "B2B trade content",
            "personnel announcements",
            "political content",
            "obituaries",
            "competitor bashing",
        ],
    },
}


# ─────────────────────────────────────────────
# Email Template Configuration
# ─────────────────────────────────────────────

EMAIL_TEMPLATE_CONFIG = {
    "template_file": "templates/consumer-newsletter-email.html",
    "container_width": 680,
    "font_family": "'Wix Madefor Display', Arial, sans-serif",
    "colors": {
        "header_bg": "#272d3f",
        "intro_bg": "#f2f2f2",
        "section_header_badge": "#008181",
        "section_dark_bg": "#466f88",
        "body_text_dark": "#282e40",
        "body_text_light": "#ffffff",
        "intro_text": "#4b4b4b",
        "accent_teal": "#31D7CA",
        "accent_orange": "#fe8916",
        "border_teal": "#008181",
        "footer_bg": "#272d3e",
    },
    "font_sizes": {
        "section_header": "26px",
        "body_text": "16px",
        "intro_text": "20px",
        "small_text": "13px",
    },
}


# ─────────────────────────────────────────────
# AI Prompt Templates
# ─────────────────────────────────────────────

AI_PROMPTS = {
    "generate_intro": (
        "Write a witty, engaging 1-2 sentence newsletter intro for the {month} "
        "issue of BriteCo's consumer jewelry newsletter. The intro should:\n"
        "- Open with a pop culture reference, seasonal hook, or clever observation\n"
        "- Tie back to jewelry or the content highlights\n"
        "- Feel like a fun friend texting — conversational and warm\n"
        "- Use italic-worthy phrasing\n"
        "- Max 40 words\n"
        "- Do NOT include any label, prefix, or heading like 'Newsletter Intro:' — "
        "return ONLY the intro text itself\n\n"
        "Content highlights this month: {highlights}\n\n"
        "Examples of past intros:\n"
        "- 'This holiday season, take a page out of Liz Taylor's book—or jewelry box, "
        "rather—and treat yourself to something that sparkles as much as you do.'\n"
        "- 'PSL's may be over, but sparkle season is just getting started.'\n"
        "- 'New year, new satisfying piece of ice—who needs resolutions when you've got carats?'"
    ),
    "generate_whats_inside": (
        "Generate 4 'What's Inside' bullet items for a consumer jewelry newsletter. "
        "Each bullet should:\n"
        "- Start with a relevant emoji\n"
        "- Tease the section content without giving everything away\n"
        "- Be one short, catchy line\n"
        "- Build curiosity\n\n"
        "Sections to tease:\n{sections}\n\n"
        "Examples:\n"
        "- 💍 The viral video jewelers don't want you to see\n"
        "- 🔥 Lab-grown vs. natural: the trend that's dividing the industry\n"
        "- 📖 Two must-read guides for protecting your bling\n"
        "- 💎 Can you guess the price of this high-profile rock?"
    ),
    "generate_video_description": (
        "Write a {max_words}-word description for a YouTube video to include "
        "in a consumer jewelry newsletter.\n\n"
        "Video title: {title}\n"
        "Video description: {description}\n\n"
        "Guidelines:\n"
        "- 3-4 sentences summarizing the key takeaway\n"
        "- Consumer-friendly language — no industry jargon\n"
        "- End with a hook encouraging the reader to watch\n"
        "- Conversational, engaging tone\n"
        "- Max {max_words} words\n"
        "- Do NOT include any label, prefix, or title like 'Featured Video:', "
        "'Video Description:', or 'News of the Month:' — return ONLY the "
        "description paragraph"
    ),
    "generate_guess_the_price_details": (
        "Generate details for a 'Guess the Price' jewelry newsletter section.\n\n"
        "Item: {title}\n"
        "Source URL: {url}\n"
        "Context: {snippet}\n\n"
        "Provide these 4 fields:\n"
        "1. Material (max 15 words): Primary materials and key specs\n"
        "2. Found In (max 15 words): Where it was discovered, sold, or featured\n"
        "3. Where It Lives (max 15 words): Current home or owner type\n"
        "4. Fun Fact (max 20 words): An intriguing, shareable piece of trivia\n\n"
        "IMPORTANT: Do NOT include, mention, or hint at the price or value of the item "
        "in any of the fields. The entire point is for readers to guess the price.\n\n"
        "Also suggest a teasing question that builds suspense about the price "
        "(without revealing or hinting at the actual price).\n\n"
        "Return as JSON: {{\"material\": \"...\", \"found_in\": \"...\", "
        "\"where_it_lives\": \"...\", \"fun_fact\": \"...\", \"suggested_question\": \"...\"}}"
    ),
    "generate_quick_tip": (
        "Write a quick jewelry care or styling tip for the {month} issue of a "
        "consumer newsletter.\n\n"
        "Season: {season}\n"
        "Suggested themes: {themes}\n\n"
        "Guidelines:\n"
        "- Practical, actionable advice readers can use immediately\n"
        "- Tied to the current season or upcoming events\n"
        "- Friendly, helpful tone — like a knowledgeable friend\n"
        "- 1-2 short paragraphs\n"
        "- Max 60 words\n"
        "- Do not use bullet points — flowing prose only\n"
        "- Do NOT include a title, heading, or label — return ONLY the tip text"
    ),
    "generate_subject_lines": (
        "Generate 5 email subject lines AND 5 matching preheader texts for a consumer jewelry newsletter.\n\n"
        "Month: {month} {year}\n"
        "Key content: {highlights}\n\n"
        "Subject Line Guidelines:\n"
        "- Mix of curiosity-driven, benefit-driven, and playful approaches\n"
        "- 40-60 characters ideal\n"
        "- Use emojis sparingly (max 1 per subject line, or none)\n"
        "- Reference specific content from this issue when possible\n"
        "- No clickbait — deliver on the promise\n\n"
        "Preheader Guidelines:\n"
        "- 40-90 characters ideal\n"
        "- Complement (don't repeat) the subject line\n"
        "- Tease content to encourage opening\n"
        "- Each preheader should pair with the corresponding subject line\n\n"
        "Return as JSON: {{\"subject_lines\": [\"...\", ...], \"preheaders\": [\"...\", ...]}}"
    ),
    "brand_check": (
        "Review this consumer newsletter content against BriteCo editorial guidelines.\n\n"
        "Check for:\n"
        "1. Tone: Friendly, fun, engaging (not B2B or overly formal)\n"
        "2. BriteCo spelling (capital B, capital C, one word)\n"
        "3. Serial/Oxford comma usage\n"
        "4. Em dashes with no spaces\n"
        "5. Numbers: spell out 1-9, numerals for 10+\n"
        "6. Percentages use % symbol\n"
        "7. Lab-grown is hyphenated\n"
        "8. Title case on section headers\n"
        "9. Inclusive language (partner/spouse, singular they)\n"
        "10. No fear-based insurance language\n"
        "11. No B2B jargon\n"
        "12. Word count limits respected\n\n"
        "Content to review:\n{content}\n\n"
        "Word count limits:\n"
        "- Intro: 40 words\n"
        "- Video descriptions: 80 words each\n"
        "- Quick Tip: 60 words\n"
        "- Guess the Price detail fields: 20 words each\n\n"
        "Return a JSON object with:\n"
        "- passed: boolean (true if no issues found)\n"
        "- score: number (0-100)\n"
        "- suggestions: array of objects, each with:\n"
        "  - section: one of 'intro', 'news_of_month', 'trend_alert', 'guess_the_price', 'quick_tip'\n"
        "  - original: the exact text that needs changing (copy it verbatim from the content)\n"
        "  - suggested: the corrected replacement text\n"
        "  - reason: brief explanation of why this change is needed\n"
        "  - severity: 'error' or 'warning'\n\n"
        "IMPORTANT: For each suggestion, 'original' must be an exact substring from the content so it can be found and highlighted."
    ),
}


# ─────────────────────────────────────────────
# Season Mapping
# ─────────────────────────────────────────────

MONTH_TO_SEASON = {
    "january": "winter",
    "february": "winter",
    "march": "spring",
    "april": "spring",
    "may": "spring",
    "june": "summer",
    "july": "summer",
    "august": "summer",
    "september": "fall",
    "october": "fall",
    "november": "fall",
    "december": "winter",
}
