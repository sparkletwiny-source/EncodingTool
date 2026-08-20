from flask import Flask, request, render_template_string
import base64
import html
import json
import urllib.parse
import re
import random
import os


app = Flask(__name__)


# ============================================================
# CHARACTER SETS
# ============================================================

CHARSETS = {

    # Unicode
    "utf-8": "UTF-8",
    "utf-16": "UTF-16",
    "utf-16-le": "UTF-16 LE",
    "utf-16-be": "UTF-16 BE",
    "utf-32": "UTF-32",
    "utf-32-le": "UTF-32 LE",
    "utf-32-be": "UTF-32 BE",

    # US / Western
    "us-ascii": "US-ASCII",
    "ascii": "ASCII",
    "iso-8859-1": "ISO-8859-1 / Latin-1",
    "iso-8859-15": "ISO-8859-15 / Latin-9",
    "windows-1252": "Windows-1252",
    "cp1252": "Windows-1252",

    # Central / Eastern European
    "iso-8859-2": "ISO-8859-2 / Latin-2",
    "windows-1250": "Windows-1250",
    "cp1250": "Windows-1250",
    "iso-8859-4": "ISO-8859-4",
    "iso-8859-13": "ISO-8859-13",
    "iso-8859-16": "ISO-8859-16",

    # Cyrillic
    "iso-8859-5": "ISO-8859-5",
    "windows-1251": "Windows-1251",
    "cp1251": "Windows-1251",
    "koi8-r": "KOI8-R",
    "koi8-u": "KOI8-U",

    # Greek
    "iso-8859-7": "ISO-8859-7 / Greek",
    "windows-1253": "Windows-1253",
    "cp1253": "Windows-1253",

    # Hebrew
    "iso-8859-8": "ISO-8859-8 / Hebrew",
    "windows-1255": "Windows-1255",
    "cp1255": "Windows-1255",

    # Arabic
    "iso-8859-6": "ISO-8859-6 / Arabic",
    "windows-1256": "Windows-1256",
    "cp1256": "Windows-1256",

    # Turkish
    "iso-8859-9": "ISO-8859-9 / Latin-5",
    "windows-1254": "Windows-1254",
    "cp1254": "Windows-1254",

    # Baltic
    "windows-1257": "Windows-1257",
    "cp1257": "Windows-1257",

    # Japanese
    "shift_jis": "Shift_JIS",
    "shift-jis": "Shift_JIS",
    "euc_jp": "EUC-JP",
    "euc-jp": "EUC-JP",
    "iso-2022-jp": "ISO-2022-JP",

    # Chinese
    "gb2312": "GB2312",
    "gbk": "GBK",
    "gb18030": "GB18030",
    "big5": "Big5",
    "big5-hkscs": "Big5-HKSCS",
    "hz": "HZ-GB-2312",

    # Korean
    "euc_kr": "EUC-KR",
    "euc-kr": "EUC-KR",
    "iso-2022-kr": "ISO-2022-KR",

    # Thai
    "tis-620": "TIS-620",
    "windows-874": "Windows-874",

    # Other legacy
    "mac-roman": "Mac Roman",
    "mac_cyrillic": "Mac Cyrillic",
    "cp437": "IBM PC / CP437",
    "cp850": "IBM PC / CP850",
    "cp852": "IBM PC / CP852",
    "cp866": "IBM PC / CP866",
}


# ============================================================
# CODECS
# ============================================================

CODECS = {

    # Unicode
    "utf-8": "utf-8",
    "utf-16": "utf-16",
    "utf-16-le": "utf-16-le",
    "utf-16-be": "utf-16-be",
    "utf-32": "utf-32",
    "utf-32-le": "utf-32-le",
    "utf-32-be": "utf-32-be",

    # ASCII / Western
    "us-ascii": "ascii",
    "ascii": "ascii",
    "iso-8859-1": "iso-8859-1",
    "iso-8859-15": "iso-8859-15",
    "windows-1252": "cp1252",
    "cp1252": "cp1252",

    # Central / Eastern
    "iso-8859-2": "iso-8859-2",
    "windows-1250": "cp1250",
    "cp1250": "cp1250",
    "iso-8859-4": "iso-8859-4",
    "iso-8859-13": "iso-8859-13",
    "iso-8859-16": "iso-8859-16",

    # Cyrillic
    "iso-8859-5": "iso-8859-5",
    "windows-1251": "cp1251",
    "cp1251": "cp1251",
    "koi8-r": "koi8-r",
    "koi8-u": "koi8-u",

    # Greek
    "iso-8859-7": "iso-8859-7",
    "windows-1253": "cp1253",
    "cp1253": "cp1253",

    # Hebrew
    "iso-8859-8": "iso-8859-8",
    "windows-1255": "cp1255",
    "cp1255": "cp1255",

    # Arabic
    "iso-8859-6": "iso-8859-6",
    "windows-1256": "cp1256",
    "cp1256": "cp1256",

    # Turkish
    "iso-8859-9": "iso-8859-9",
    "windows-1254": "cp1254",
    "cp1254": "cp1254",

    # Baltic
    "windows-1257": "cp1257",
    "cp1257": "cp1257",

    # Japanese
    "shift_jis": "shift_jis",
    "shift-jis": "shift_jis",
    "euc_jp": "euc_jp",
    "euc-jp": "euc_jp",
    "iso-2022-jp": "iso2022_jp",

    # Chinese
    "gb2312": "gb2312",
    "gbk": "gbk",
    "gb18030": "gb18030",
    "big5": "big5",
    "big5-hkscs": "big5hkscs",
    "hz": "hz",

    # Korean
    "euc_kr": "euc_kr",
    "euc-kr": "euc_kr",
    "iso-2022-kr": "iso2022_kr",

    # Thai
    "tis-620": "tis-620",
    "windows-874": "cp874",

    # Legacy
    "mac-roman": "mac_roman",
    "mac_cyrillic": "mac_cyrillic",
    "cp437": "cp437",
    "cp850": "cp850",
    "cp852": "cp852",
    "cp866": "cp866",
}


# ============================================================
# ENCODING METHODS
# ============================================================

METHODS = {
    "q": "Quoted-Printable / RFC 2047 Q",
    "base64": "Base64 / RFC 2047 B",
    "url": "URL / Percent Encoding",
    "html": "HTML Entity Encoding",
    "hex": "Hexadecimal",
    "unicode": "Unicode Escape",
    "json": "JSON Unicode Escape",
    "punycode": "Punycode",
}


# ============================================================
# ADD CHUNKED Q METHOD FOR EVERY CHARSET
# ============================================================

for charset_key, charset_name in CHARSETS.items():

    # Avoid duplicate methods for aliases
    method_key = f"{charset_key}-q-chunked"

    METHODS[method_key] = (
        f"{charset_name} Q / Chunked RFC 2047"
    )

# ============================================================
# ADD SPACES AFTER WORDS
# ============================================================

def add_spaces_after_words(text, count):

    if count <= 0:
        return text

    return re.sub(
        r"(\S+)(?=\s|$)",
        lambda m: m.group(1) + (" " * count),
        text
    )


# ============================================================
# QUOTED PRINTABLE - UNLIMITED SINGLE BLOCK
# ============================================================

def q_encode_bytes(data, space_hex=False):

    result = []

    for b in data:

        # Space
        if b == 0x20:

            if space_hex:
                result.append("=20")
            else:
                # RFC 2047 Q representation
                result.append("_")

        # Everything else is encoded as =XX
        else:

            result.append(
                f"={b:02X}"
            )

    return "".join(result)

# ============================================================
# SPLIT RFC 2047 Q ENCODED WORDS
# Maximum encoded-word length = 75 characters
# ============================================================

def split_q_encoded_words(
    encoded,
    max_length=75
):

    # --------------------------------------------------------
    # Find RFC 2047 prefix
    #
    # Example:
    # =?UTF-8?Q?
    # --------------------------------------------------------

    prefix_end = encoded.find("?Q?")

    if prefix_end == -1:
        return encoded

    prefix = encoded[
        :prefix_end + 3
    ]

    # --------------------------------------------------------
    # Must end with ?=
    # --------------------------------------------------------

    if not encoded.endswith("?="):
        return encoded

    # --------------------------------------------------------
    # Extract Q payload
    # --------------------------------------------------------

    payload = encoded[
        prefix_end + 3:-2
    ]

    suffix = "?="

    # --------------------------------------------------------
    # Available payload length
    #
    # Total encoded-word must not exceed 75 chars.
    # --------------------------------------------------------

    available = (
        max_length
        - len(prefix)
        - len(suffix)
    )

    if available <= 0:
        return encoded

    chunks = []

    current = ""

    i = 0

    # --------------------------------------------------------
    # Split payload without breaking =XX
    # --------------------------------------------------------

    while i < len(payload):

        # ----------------------------------------------------
        # Q encoded byte
        #
        # Example:
        # =E2
        # =82
        # =AC
        # ----------------------------------------------------

        if (
            payload[i] == "="
            and i + 2 < len(payload)
            and re.fullmatch(
                r"[0-9A-Fa-f]{2}",
                payload[i + 1:i + 3]
            )
        ):

            token = payload[
                i:i + 3
            ]

        else:

            token = payload[i]

        # ----------------------------------------------------
        # If adding token exceeds limit,
        # create a new chunk.
        # ----------------------------------------------------

        if (
            len(current)
            + len(token)
            > available
        ):

            if current:

                chunks.append(
                    current
                )

            current = token

        else:

            current += token

        i += len(token)

    # --------------------------------------------------------
    # Add final chunk
    # --------------------------------------------------------

    if current:

        chunks.append(
            current
        )

    # --------------------------------------------------------
    # Create separate RFC 2047 encoded-words
    #
    # Two spaces between encoded-words is intentional.
    # --------------------------------------------------------

    return "  ".join(
        prefix
        + chunk
        + suffix
        for chunk in chunks
    )


# ============================================================
# QUOTED PRINTABLE / RFC 2047 Q ENCODER
# ============================================================

def encode_q(
    text,
    charset,
    space_hex=False,
    chunked=False
):

    # --------------------------------------------------------
    # Convert text to selected charset
    # --------------------------------------------------------

    data = text.encode(
        CODECS[charset]
    )

    # --------------------------------------------------------
    # Convert bytes to RFC 2047 Q encoding
    # --------------------------------------------------------

    encoded = q_encode_bytes(
        data,
        space_hex
    )

    # --------------------------------------------------------
    # Create complete RFC 2047 encoded-word
    # --------------------------------------------------------

    full_encoded = (
        f"=?{charset.upper()}?Q?"
        f"{encoded}"
        f"?="
    )

    # --------------------------------------------------------
    # Normal Q
    # --------------------------------------------------------

    if not chunked:

        return full_encoded

    # --------------------------------------------------------
    # Chunked Q
    # --------------------------------------------------------

    return split_q_encoded_words(
        full_encoded,
        max_length=75
    )


def encode_q(
    text,
    charset,
    space_hex=False,
    chunked=False
):

    data = text.encode(
        CODECS[charset]
    )

    encoded = q_encode_bytes(
        data,
        space_hex
    )

    full_encoded = (
        f"=?{charset.upper()}?Q?"
        f"{encoded}"
        f"?="
    )

    if not chunked:

        return full_encoded

    return split_q_encoded_words(
        full_encoded,
        max_length=75
    )

    # ========================================================
    # IMPORTANT:
    #
    # NO 75 CHARACTER LIMIT
    # NO SPLITTING
    # NO LINE WRAPPING
    #
    # Entire input becomes ONE encoded block.
    # ========================================================

    return (
        f"=?{charset.upper()}?Q?"
        f"{encoded}"
        f"?="
    )


# ============================================================
# BASE64
# ============================================================

def encode_base64(
    text,
    charset
):

    data = text.encode(
        CODECS[charset]
    )

    encoded = base64.b64encode(
        data
    ).decode("ascii")

    return (
        f"=?{charset.upper()}?B?"
        f"{encoded}"
        f"?="
    )


# ============================================================
# OTHER ENCODINGS
# ============================================================

def encode_other(
    text,
    charset,
    method
):

    data = text.encode(
        CODECS[charset]
    )

    if method == "url":

        return urllib.parse.quote(
            data,
            safe=""
        )

    if method == "html":

        return html.escape(
            text
        )

    if method == "hex":

        return data.hex(" ")

    if method == "unicode":

        return "".join(
            f"\\u{ord(c):04X}"
            for c in text
        )

    if method == "json":

        return json.dumps(
            text,
            ensure_ascii=True
        )

    if method == "punycode":

        return text.encode(
            "punycode"
        ).decode("ascii")

    raise ValueError(
        "Unsupported encoding method"
    )


def encode_text(
    text,
    charset,
    method,
    space_hex
):

    # Normal Q
    if method == "q":

        return encode_q(
            text,
            charset,
            space_hex,
            chunked=False
        )

    # Any charset-specific chunked Q
    if method.endswith("-q-chunked"):

        chunked_charset = method[
            :-len("-q-chunked")
        ]

        if chunked_charset not in CHARSETS:

            raise ValueError(
                f"Unsupported chunked Q charset: "
                f"{chunked_charset}"
            )

        return encode_q(
            text,
            chunked_charset,
            space_hex,
            chunked=True
        )

    # Base64
    if method == "base64":

        return encode_base64(
            text,
            charset
        )

    # Other methods
    return encode_other(
        text,
        charset,
        method
    )
# ============================================================
# ENCODE SELECTED ITEMS
# ============================================================

def encode_selected_items(
    text,
    selected_items,
    charset,
    method,
    space_hex
):

    # --------------------------------------------------------
    # No selected items
    # --------------------------------------------------------

    if not selected_items.strip():

        return text

    # --------------------------------------------------------
    # Split selected items
    # --------------------------------------------------------

    items = [
        x.strip()
        for x in selected_items.split(",")
        if x.strip()
    ]

    if not items:

        return text

    # --------------------------------------------------------
    # Longest first
    # --------------------------------------------------------

    items.sort(
        key=len,
        reverse=True
    )

    # --------------------------------------------------------
    # Create regex
    # --------------------------------------------------------

    pattern = "|".join(
        re.escape(item)
        for item in items
    )

    regex = re.compile(
        pattern
    )

    # --------------------------------------------------------
    # Replacement
    # --------------------------------------------------------

    def replacement(match):

        value = match.group(0)

        return encode_text(
            value,
            charset,
            method,
            space_hex
        )

    # --------------------------------------------------------
    # Replace selected items
    # --------------------------------------------------------

    return regex.sub(
        replacement,
        text
    )


# ============================================================
# RANDOMLY ENCODE SELECTED ITEMS
# ============================================================

def encode_random_selected_items(
    text,
    selected_items,
    charset,
    method,
    space_hex,
    random_percentage=50
):

    # --------------------------------------------------------
    # Validate percentage
    # --------------------------------------------------------

    random_percentage = max(
        1,
        min(
            random_percentage,
            100
        )
    )

    # ========================================================
    # SPECIFIC ITEMS
    # ========================================================

    if selected_items.strip():

        # ----------------------------------------------------
        # Split selected items
        # ----------------------------------------------------

        items = [
            x.strip()
            for x in selected_items.split(",")
            if x.strip()
        ]

        if not items:

            return text

        # ----------------------------------------------------
        # Longest first
        # ----------------------------------------------------

        items.sort(
            key=len,
            reverse=True
        )

        # ----------------------------------------------------
        # Create regex
        # ----------------------------------------------------

        pattern = "|".join(
            re.escape(item)
            for item in items
        )

        regex = re.compile(
            pattern
        )

        # ----------------------------------------------------
        # Random replacement
        # ----------------------------------------------------

        def replacement(match):

            value = match.group(0)

            chance = random.randint(
                1,
                100
            )

            if chance <= random_percentage:

                return encode_text(
                    value,
                    charset,
                    method,
                    space_hex
                )

            return value

        # ----------------------------------------------------
        # Replace randomly
        # ----------------------------------------------------

        return regex.sub(
            replacement,
            text
        )

    # ========================================================
    # AUTOMATIC WORD SELECTION
    # ========================================================

    word_pattern = r"\b[\w]+\b"

    # --------------------------------------------------------
    # Random word replacement
    # --------------------------------------------------------

    def random_word_replacement(match):

        value = match.group(0)

        # ----------------------------------------------------
        # Skip one-character words
        # ----------------------------------------------------

        if len(value) <= 1:

            return value

        # ----------------------------------------------------
        # Random chance
        # ----------------------------------------------------

        chance = random.randint(
            1,
            100
        )

        if chance <= random_percentage:

            return encode_text(
                value,
                charset,
                method,
                space_hex
            )

        return value

    # --------------------------------------------------------
    # Replace random words
    # --------------------------------------------------------

    return re.sub(
        word_pattern,
        random_word_replacement,
        text
    )


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Email Encoding Tool</title>

<style>

/* ============================================================
   GLOBAL
   ============================================================ */

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    min-height: 100%;
}

body {

    min-height: 100vh;

    padding: 14px;

    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    color: #eef6ff;

    background:
        radial-gradient(
            circle at 5% 5%,
            rgba(0, 229, 255, 0.20),
            transparent 27%
        ),
        radial-gradient(
            circle at 95% 5%,
            rgba(168, 85, 247, 0.24),
            transparent 28%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(59, 130, 246, 0.18),
            transparent 32%
        ),
        linear-gradient(
            135deg,
            #030712 0%,
            #071426 45%,
            #10152b 100%
        );

    background-attachment: fixed;

    overflow-x: hidden;
}


/* ============================================================
   MAIN CONTAINER
   ============================================================ */

.container {

    width: 100%;

    max-width: 1500px;

    min-height:
        calc(100vh - 28px);

    margin: 0 auto;

    padding: 20px 24px;

    border:
        1px solid
        rgba(125, 211, 252, 0.20);

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(8, 20, 39, 0.97),
            rgba(15, 23, 42, 0.95)
        );

    box-shadow:
        0 30px 80px
        rgba(0, 0, 0, 0.50),

        inset 0 1px 0
        rgba(255, 255, 255, 0.07);

    backdrop-filter:
        blur(20px);

    -webkit-backdrop-filter:
        blur(20px);
}


/* ============================================================
   HEADER
   ============================================================ */

.header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    margin-bottom: 15px;

    padding:
        2px 4px 12px;

    border-bottom:
        1px solid
        rgba(148, 163, 184, 0.12);
}

h1 {

    margin: 0;

    font-size: 30px;

    line-height: 1.1;

    font-weight: 800;

    letter-spacing: -0.7px;

    background:
        linear-gradient(
            90deg,
            #38bdf8 0%,
            #818cf8 45%,
            #c084fc 75%,
            #22d3ee 100%
        );

    -webkit-background-clip: text;

    background-clip: text;

    color: transparent;

    text-shadow:
        0 0 28px
        rgba(56, 189, 248, 0.18);
}


/* ============================================================
   TWO COLUMN MAIN LAYOUT
   ============================================================ */

.main-grid {

    display: grid;

    grid-template-columns:
        minmax(0, 1.08fr)
        minmax(0, 0.92fr);

    gap: 18px;

    align-items: start;
}


/* ============================================================
   PANELS
   ============================================================ */

.left-panel,
.right-panel {

    min-width: 0;

    padding: 15px;

    border:
        1px solid
        rgba(96, 165, 250, 0.14);

    border-radius: 16px;

    background:
        linear-gradient(
            145deg,
            rgba(15, 31, 55, 0.72),
            rgba(15, 23, 42, 0.58)
        );

    box-shadow:
        inset 0 1px 0
        rgba(255, 255, 255, 0.035);
}


/* ============================================================
   LABELS
   ============================================================ */

label {

    display: block;

    margin-top: 12px;

    margin-bottom: 6px;

    font-size: 14px;

    font-weight: 750;

    letter-spacing: 0.1px;

    color: #d9efff;

    text-shadow:
        0 1px 10px
        rgba(56, 189, 248, 0.08);
}

label:first-child {
    margin-top: 0;
}


/* ============================================================
   INPUTS
   ============================================================ */

textarea,
select,
input[type="number"],
input[type="text"] {

    width: 100%;

    border:
        1px solid
        rgba(100, 116, 139, 0.65);

    border-radius: 10px;

    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    font-size: 14px;

    font-weight: 500;

    background:
        linear-gradient(
            145deg,
            rgba(5, 15, 30, 0.94),
            rgba(15, 23, 42, 0.94)
        );

    color: #f4f9ff;

    outline: none;

    transition:
        all 0.20s ease;

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,0.035);
}


/* ============================================================
   TEXTAREA
   ============================================================ */

textarea {

    min-height: 112px;

    height: 112px;

    padding: 12px 14px;

    resize: vertical;

    line-height: 1.55;

    color: #e8f7ff;
}


/* ============================================================
   SELECT + TEXT + NUMBER
   ============================================================ */

select,
input[type="number"],
input[type="text"] {

    min-height: 44px;

    padding:
        9px 12px;
}

select {
    cursor: pointer;
}


/* ============================================================
   PLACEHOLDER
   ============================================================ */

textarea::placeholder,
input::placeholder {

    color: #7186a3;

    opacity: 1;
}


/* ============================================================
   FOCUS
   ============================================================ */

textarea:focus,
select:focus,
input[type="number"]:focus,
input[type="text"]:focus {

    border-color:
        #38bdf8;

    background:
        linear-gradient(
            145deg,
            rgba(8, 24, 45, 0.98),
            rgba(20, 30, 55, 0.98)
        );

    box-shadow:
        0 0 0 3px
        rgba(56, 189, 248, 0.10),

        0 0 25px
        rgba(56, 189, 248, 0.10),

        inset 0 1px 0
        rgba(255,255,255,0.05);
}


/* ============================================================
   SELECT OPTIONS
   ============================================================ */

select option {

    background: #0b1628;

    color: #f8fbff;
}


/* ============================================================
   CHARACTER + FORMAT SIDE BY SIDE
   ============================================================ */

.encoding-row {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 12px;

    margin-top: 2px;
}

.encoding-field {
    min-width: 0;
}

.encoding-field label {
    margin-top: 0;
}


/* ============================================================
   GENERAL BOX
   ============================================================ */

.box {

    margin-top: 12px;

    padding: 13px 15px;

    border:
        1px solid
        rgba(96, 165, 250, 0.18);

    border-radius: 12px;

    background:
        linear-gradient(
            145deg,
            rgba(30, 64, 100, 0.25),
            rgba(15, 23, 42, 0.70)
        );

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,0.035),

        0 8px 25px
        rgba(0,0,0,0.10);
}


/* ============================================================
   BOX TITLE
   ============================================================ */

.box > strong {

    display: block;

    margin-bottom: 8px;

    font-size: 14px;

    font-weight: 800;

    color: #7dd3fc;

    letter-spacing: 0.2px;
}


/* ============================================================
   OPTIONS
   ============================================================ */

.option {

    margin: 7px 0;

    padding: 7px 9px;

    border-radius: 8px;

    color: #cfe6f8;

    background:
        rgba(255,255,255,0.025);

    transition:
        background 0.18s ease;
}

.option:hover {

    background:
        rgba(56,189,248,0.06);
}

.option label {

    display: inline;

    margin: 0;

    font-size: 13px;

    font-weight: 550;

    color: #d4e7f5;

    cursor: pointer;
}


/* ============================================================
   RADIO / CHECKBOX
   ============================================================ */

input[type="radio"],
input[type="checkbox"] {

    margin-right: 7px;

    accent-color: #38bdf8;

    transform:
        translateY(1px);

    cursor: pointer;
}


/* ============================================================
   RANDOM SETTINGS
   ============================================================ */

.random-settings {

    display: block;

    margin-top: 8px;

    padding: 9px 11px;

    border:
        1px dashed
        rgba(192, 132, 252, 0.40);

    border-radius: 9px;

    background:
        linear-gradient(
            135deg,
            rgba(91, 33, 182, 0.13),
            rgba(59, 7, 100, 0.10)
        );
}

.random-settings label {

    margin-bottom: 4px;

    font-size: 12px;

    color: #d8b4fe;
}

.random-settings input[type="number"] {

    width: 100%;

    min-height: 34px;

    height: 34px;

    padding: 5px 9px;

    font-size: 13px;
}


/* ============================================================
   HELP TEXT
   ============================================================ */

.help {

    margin-top: 4px;

    color: #8195ae;

    font-size: 11px;

    line-height: 1.35;
}


/* ============================================================
   BUTTON
   ============================================================ */

button {

    border: 0;

    border-radius: 10px;

    background:
        linear-gradient(
            135deg,
            #0284c7,
            #2563eb 45%,
            #7c3aed
        );

    color: #ffffff;

    cursor: pointer;

    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    font-size: 14px;

    font-weight: 800;

    letter-spacing: 0.15px;

    box-shadow:
        0 8px 24px
        rgba(37, 99, 235, 0.28),

        inset 0 1px 0
        rgba(255,255,255,0.20);

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease,
        filter 0.18s ease;
}

button:hover {

    filter: brightness(1.08);

    transform:
        translateY(-1px);

    box-shadow:
        0 12px 30px
        rgba(37, 99, 235, 0.38),

        inset 0 1px 0
        rgba(255,255,255,0.22);
}

button:active {

    transform:
        translateY(0);
}


/* ============================================================
   ENCODE BUTTON
   ============================================================ */

.left-panel form > button {

    width: 100%;

    height: 45px;

    margin-top: 13px;

    font-size: 15px;
}


/* ============================================================
   COPY BUTTON
   ============================================================ */

.copy {

    margin: 0;

    padding:
        8px 14px;

    min-width: 105px;

    background:
        linear-gradient(
            135deg,
            #334155,
            #475569
        );

    box-shadow:
        0 6px 18px
        rgba(0,0,0,0.20);
}

.copy:hover {

    box-shadow:
        0 8px 22px
        rgba(0,0,0,0.30);
}


/* ============================================================
   RESULT HEADER
   ============================================================ */

.result-header {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 10px;

    margin-bottom: 7px;
}

.result-header label {

    margin: 0;

    font-size: 15px;

    color: #7dd3fc;
}


/* ============================================================
   RESULT AREA
   ============================================================ */

pre {

    white-space: pre-wrap;

    word-break: break-all;

    margin: 0;

    padding: 14px;

    min-height: 235px;

    max-height: 51vh;

    overflow-y: auto;

    border:
        1px solid
        rgba(71, 85, 105, 0.75);

    border-radius: 11px;

    background:
        linear-gradient(
            145deg,
            rgba(2, 8, 23, 0.98),
            rgba(9, 20, 38, 0.98)
        );

    color: #86efac;

    font-family:
        Consolas,
        "Courier New",
        monospace;

    font-size: 12px;

    line-height: 1.55;

    box-shadow:
        inset 0 1px 12px
        rgba(0,0,0,0.20);
}


/* ============================================================
   RESULT INFO BOX
   ============================================================ */

.right-panel .box {

    margin-top: 11px;

    padding: 11px 14px;

    font-size: 12px;

    line-height: 1.45;

    color: #c8d9ea;
}

.right-panel .box strong {

    display: inline;

    margin: 0;

    color: #67e8f9;

    font-weight: 750;
}


/* ============================================================
   ERROR
   ============================================================ */

.error {

    margin-top: 10px;

    padding: 10px 12px;

    border:
        1px solid
        rgba(248, 113, 113, 0.28);

    border-radius: 9px;

    background:
        rgba(127, 29, 29, 0.30);

    color: #fecaca;

    font-size: 12px;

    line-height: 1.4;
}


/* ============================================================
   THEME BUTTON
   ============================================================ */

.theme-toggle {

    position: fixed;

    top: 12px;

    right: 16px;

    z-index: 9999;

    margin: 0;

    padding:
        7px 13px;

    width: auto;

    min-height: 32px;

    border:
        1px solid
        rgba(148, 163, 184, 0.30);

    border-radius: 20px;

    background:
        rgba(8, 20, 39, 0.90);

    color: #e0f2fe;

    backdrop-filter:
        blur(12px);

    box-shadow:
        0 8px 22px
        rgba(0,0,0,0.25);

    font-size: 11px;

    cursor: pointer;
}

.theme-toggle:hover {

    transform: none;

    filter: brightness(1.08);
}


/* ============================================================
   SCROLLBAR
   ============================================================ */

::-webkit-scrollbar {

    width: 7px;

    height: 7px;
}

::-webkit-scrollbar-track {

    background:
        rgba(15, 23, 42, 0.55);
}

::-webkit-scrollbar-thumb {

    background:
        linear-gradient(
            #2563eb,
            #7c3aed
        );

    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {

    background:
        linear-gradient(
            #38bdf8,
            #a78bfa
        );
}


/* ============================================================
   LIGHT MODE
   ============================================================ */

body.light-mode {

    color: #172033;

    background:
        radial-gradient(
            circle at 5% 5%,
            rgba(14, 165, 233, 0.16),
            transparent 27%
        ),

        radial-gradient(
            circle at 95% 5%,
            rgba(139, 92, 246, 0.14),
            transparent 28%
        ),

        linear-gradient(
            135deg,
            #edf7ff,
            #f8fafc,
            #eef2ff
        );
}


body.light-mode .container {

    background:
        rgba(255,255,255,0.94);

    border-color:
        rgba(100,116,139,0.20);

    box-shadow:
        0 25px 70px
        rgba(15,23,42,0.14);
}


body.light-mode .left-panel,
body.light-mode .right-panel {

    background:
        linear-gradient(
            145deg,
            rgba(241,245,249,0.90),
            rgba(255,255,255,0.88)
        );

    border-color:
        rgba(100,116,139,0.17);
}


body.light-mode label {

    color: #243b53;
}


body.light-mode textarea,
body.light-mode select,
body.light-mode input[type="number"],
body.light-mode input[type="text"] {

    background:
        linear-gradient(
            145deg,
            #ffffff,
            #f8fafc
        );

    color: #172033;

    border-color:
        #cbd5e1;
}


body.light-mode textarea::placeholder,
body.light-mode input::placeholder {

    color: #8292a8;
}


body.light-mode select option {

    background: #ffffff;

    color: #172033;
}


body.light-mode .box {

    background:
        linear-gradient(
            145deg,
            #f1f7fb,
            #ffffff
        );

    border-color:
        #dbe4ee;
}


body.light-mode .option {

    background:
        rgba(15,23,42,0.025);

    color: #475569;
}


body.light-mode .option label {

    color: #475569;
}


body.light-mode .help {

    color: #64748b;
}


body.light-mode pre {

    background:
        linear-gradient(
            145deg,
            #f8fafc,
            #eef6ff
        );

    color: #166534;

    border-color:
        #cbd5e1;
}


body.light-mode .random-settings {

    background:
        linear-gradient(
            135deg,
            rgba(237,233,254,0.75),
            rgba(245,243,255,0.85)
        );

    border-color:
        rgba(124,58,237,0.25);
}


body.light-mode .random-settings label {

    color: #6d28d9;
}


body.light-mode .theme-toggle {

    background: #ffffff;

    color: #172033;

    border-color: #cbd5e1;

    box-shadow:
        0 6px 20px
        rgba(15,23,42,0.12);
}


body.light-mode .error {

    background: #fff1f2;

    color: #9f1239;

    border-color: #fecdd3;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 1100px) {

    .main-grid {

        grid-template-columns:
            minmax(0, 1fr)
            minmax(0, 0.9fr);

        gap: 14px;
    }

    .container {

        padding: 17px;
    }

    .left-panel,
    .right-panel {

        padding: 13px;
    }
}


/* ============================================================
   TABLET / MOBILE
   ============================================================ */

@media (max-width: 850px) {

    body {

        padding: 8px;
    }

    .container {

        min-height:
            calc(100vh - 16px);

        padding: 14px;

        border-radius: 15px;
    }

    .header {

        margin-bottom: 12px;

        padding-bottom: 10px;
    }

    h1 {

        font-size: 23px;
    }

    .main-grid {

        grid-template-columns: 1fr;

        gap: 12px;
    }

    .encoding-row {

        grid-template-columns: 1fr;
    }

    .theme-toggle {

        top: 8px;

        right: 8px;
    }

    button {

        width: 100%;
    }

    .copy {

        width: auto;
    }

    .result-header {

        align-items: center;
    }

    pre {

        max-height: 45vh;

        min-height: 180px;
    }
}


/* ============================================================
   SMALL MOBILE
   ============================================================ */

@media (max-width: 500px) {

    body {

        padding: 5px;
    }

    .container {

        padding: 11px;

        border-radius: 12px;
    }

    h1 {

        font-size: 20px;
    }

    .left-panel,
    .right-panel {

        padding: 11px;
    }

    textarea {

        min-height: 105px;

        height: 105px;
    }

    .result-header {

        gap: 7px;
    }

    .copy {

        padding:
            7px 11px;

        min-width: 90px;

        font-size: 12px;
    }
}

</style>

</head>


<body>


<!-- =========================================================
     THEME TOGGLE
     ========================================================= -->

<button
    type="button"
    id="themeToggle"
    class="theme-toggle"
    onclick="toggleTheme()"
>
☀️ Light Mode
</button>


<!-- =========================================================
     MAIN CONTAINER
     ========================================================= -->

<div class="container">


<!-- =========================================================
     HEADER
     ========================================================= -->

<div class="header">

    <h1>
        Email Encoding Tool
    </h1>

</div>


<!-- =========================================================
     MAIN GRID
     ========================================================= -->

<div class="main-grid">


<!-- =========================================================
     LEFT PANEL
     ========================================================= -->

<div class="left-panel">

<form method="POST">


<!-- INPUT -->

<label>
    Input Sentence
</label>

<textarea
    name="text"
    placeholder="Example: Email Encoding Tool"
>{{ text }}</textarea>


<!-- CHARACTER + FORMAT -->

<div class="encoding-row">


    <div class="encoding-field">

        <label>
            Character Encoding
        </label>

        <select name="charset">

        {% for key, name in charsets.items() %}

        <option
            value="{{ key }}"
            {% if charset == key %}
            selected
            {% endif %}
        >
            {{ name }}
        </option>

        {% endfor %}

        </select>

    </div>


    <div class="encoding-field">

        <label>
            Encoding Format
        </label>

        <select name="method">

        {% for key, name in methods.items() %}

        <option
            value="{{ key }}"
            {% if method == key %}
            selected
            {% endif %}
        >
            {{ name }}
        </option>

        {% endfor %}

        </select>

    </div>

</div>


<!-- =========================================================
     ENCODING SELECTION
     ========================================================= -->

<div class="box">

<strong>
    Encoding Selection
</strong>


<div class="option">

<input
    type="radio"
    id="encode_all"
    name="selection_mode"
    value="all"

    {% if selection_mode == "all" %}
    checked
    {% endif %}
>

<label for="encode_all">
    Encode entire sentence
</label>

</div>


<div class="option">

<input
    type="radio"
    id="encode_selected"
    name="selection_mode"
    value="selected"

    {% if selection_mode == "selected" %}
    checked
    {% endif %}
>

<label for="encode_selected">
    Encode only specific words / characters
</label>

</div>


<div class="option">

<input
    type="radio"
    id="encode_random"
    name="selection_mode"
    value="random"

    {% if selection_mode == "random" %}
    checked
    {% endif %}
>

<label for="encode_random">
    🎲 Randomly encode selected words / letters
</label>

</div>


<div class="help">

Random mode creates a new random selection every time
you click Encode. If specific items are entered, only
those items are randomly encoded.

</div>


<!-- RANDOM % -->

<div
    class="random-settings"
    id="randomSettings"
>

<label
    for="random_percentage"
    style="margin-top:0;"
>
    Random % — 1–100% matching items
</label>

<input
    type="number"
    name="random_percentage"
    id="random_percentage"

    min="1"
    max="100"

    value="{{ random_percentage }}"
>

<div class="help">

Example: 30 = approximately 30% of matching items
will be encoded.

</div>

</div>

</div>


<!-- =========================================================
     SPECIFIC ITEMS
     ========================================================= -->

<label>
    Specific Words / Letters / Special Characters
</label>

<input
    type="text"
    name="selected_items"

    value="{{ selected_items }}"

    placeholder="Example: Clean,Today,!,@,#"
>

<div class="help">

Separate multiple items with commas.
Example: Clean,Today,!,@,#

</div>


<!-- =========================================================
     SPACES
     ========================================================= -->

<label>
    Spaces After Each Word
</label>

<input
    type="number"
    name="spaces_after_word"

    min="0"

    value="{{ spaces_after_word }}"
>

<div class="help">

Enter 0 for no additional spaces.
There is no maximum.

</div>


<!-- =========================================================
     CHECKBOX OPTIONS
     ========================================================= -->

<div class="box">


<div class="option">

<input
    type="checkbox"
    name="space_hex"
    id="space_hex"

    {% if space_hex %}
    checked
    {% endif %}
>

<label for="space_hex">

    Encode space as =20 (hex) instead of _

</label>

</div>


<div class="option">

<input
    type="checkbox"
    name="single_line"
    id="single_line"

    {% if single_line %}
    checked
    {% endif %}
>

<label for="single_line">

    Single line output

</label>

</div>


</div>


<!-- ENCODE BUTTON -->

<button type="submit">
    ⚡ Encode
</button>


</form>

</div>


<!-- =========================================================
     RIGHT PANEL
     ========================================================= -->

<div class="right-panel">


{% if result is not none %}


<div class="result-header">

<label>
    Result
</label>

<button
    type="button"
    class="copy"
    onclick="copyResult()"
>
    Copy Result
</button>

</div>


<pre id="result">{{ result }}</pre>


<div class="box">

<strong>
    Encoding:
</strong>

{{ method_name }}

<br><br>

<strong>
    Character set:
</strong>

{{ charset_name }}

<br><br>

<strong>
    Selection mode:
</strong>

{% if selection_mode == "all" %}

Entire sentence

{% elif selection_mode == "selected" %}

Specific words / characters

{% elif selection_mode == "random" %}

🎲 Randomly encoded

{% endif %}

<br><br>

<strong>
    Selected items:
</strong>

{{ selected_items if selected_items else "Automatic word selection" }}

<br><br>

<strong>
    Random percentage:
</strong>

{{ random_percentage }}%

<br><br>

<strong>
    Spaces after each word:
</strong>

{{ spaces_after_word }}

<br><br>

<strong>
    Output length:
</strong>

{{ output_length }}

</div>


{% else %}


<div class="result-header">

<label>
    Result
</label>

</div>


<pre id="result">Your encoded result will appear here.</pre>


<div class="help">

Enter your encoding options on the left,
then click <strong>Encode</strong>.

</div>


{% endif %}


{% if error %}

<div class="error">

{{ error }}

</div>

{% endif %}


</div>

</div>

</div>


<!-- =========================================================
     JAVASCRIPT
     ========================================================= -->

<script>


/* ============================================================
   COPY RESULT
   ============================================================ */

function copyResult() {

    const result =
        document.getElementById("result");

    if (!result) {
        return;
    }

    const text =
        result.innerText;

    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {

        navigator.clipboard
            .writeText(text)
            .then(function () {

                showCopyStatus();

            })
            .catch(function () {

                fallbackCopy(text);

            });

    } else {

        fallbackCopy(text);

    }

}


/* ============================================================
   FALLBACK COPY
   ============================================================ */

function fallbackCopy(text) {

    const textarea =
        document.createElement("textarea");

    textarea.value = text;

    textarea.style.position = "fixed";

    textarea.style.left = "-9999px";

    document.body.appendChild(
        textarea
    );

    textarea.focus();

    textarea.select();

    try {

        document.execCommand("copy");

        showCopyStatus();

    } catch (error) {

        console.error(
            "Copy failed:",
            error
        );

    }

    document.body.removeChild(
        textarea
    );

}


/* ============================================================
   COPY STATUS
   ============================================================ */

function showCopyStatus() {

    const buttons =
        document.querySelectorAll(".copy");

    buttons.forEach(function (button) {

        const original =
            button.innerHTML;

        button.innerHTML =
            "✓ Copied";

        setTimeout(function () {

            button.innerHTML =
                original;

        }, 1500);

    });

}


/* ============================================================
   THEME
   ============================================================ */

function toggleTheme() {

    const body =
        document.body;

    const button =
        document.getElementById(
            "themeToggle"
        );

    body.classList.toggle(
        "light-mode"
    );

    if (
        body.classList.contains(
            "light-mode"
        )
    ) {

        button.innerHTML =
            "🌙 Dark Mode";

        localStorage.setItem(
            "theme",
            "light"
        );

    } else {

        button.innerHTML =
            "☀️ Light Mode";

        localStorage.setItem(
            "theme",
            "dark"
        );

    }

}


/* ============================================================
   LOAD SAVED THEME
   ============================================================ */

(function () {

    const savedTheme =
        localStorage.getItem("theme");

    const button =
        document.getElementById(
            "themeToggle"
        );

    if (savedTheme === "light") {

        document.body.classList.add(
            "light-mode"
        );

        button.innerHTML =
            "🌙 Dark Mode";

    } else {

        button.innerHTML =
            "☀️ Light Mode";

    }

})();


/* ============================================================
   RANDOM SETTINGS VISIBILITY
   ============================================================ */

(function () {

    const radios =
        document.querySelectorAll(
            'input[name="selection_mode"]'
        );

    const settings =
        document.getElementById(
            "randomSettings"
        );


    function updateRandomSettings() {

        if (!settings) {
            return;
        }

        const selected =
            document.querySelector(
                'input[name="selection_mode"]:checked'
            );

        if (
            selected &&
            selected.value === "random"
        ) {

            settings.style.display =
                "block";

        } else {

            settings.style.display =
                "none";

        }

    }


    radios.forEach(function (radio) {

        radio.addEventListener(
            "change",
            updateRandomSettings
        );

    });


    updateRandomSettings();

})();

</script>


</body>

</html>
"""
# ============================================================
# FLASK ROUTE
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    text = ""

    charset = "utf-8"

    method = "q"

    selection_mode = "all"

    selected_items = ""

    spaces_after_word = 0

    space_hex = False

    single_line = True

    random_percentage = 50

    result = None

    error = None


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        text = request.form.get(
            "text",
            ""
        )

        charset = request.form.get(
            "charset",
            "utf-8"
        )

        method = request.form.get(
            "method",
            "q"
        )

        selection_mode = request.form.get(
            "selection_mode",
            "all"
        )

        selected_items = request.form.get(
            "selected_items",
            ""
        )


        # ----------------------------------------------------
        # CHECKBOXES
        # ----------------------------------------------------

        space_hex = (
            request.form.get(
                "space_hex"
            ) == "on"
        )

        single_line = (
            request.form.get(
                "single_line"
            ) == "on"
        )


        # ----------------------------------------------------
        # SPACES
        # ----------------------------------------------------

        try:

            spaces_after_word = int(
                request.form.get(
                    "spaces_after_word",
                    "0"
                )
            )

        except (ValueError, TypeError):

            spaces_after_word = 0


        # ----------------------------------------------------
        # RANDOM PERCENTAGE
        # ----------------------------------------------------

        try:

            random_percentage = int(
                request.form.get(
                    "random_percentage",
                    "50"
                )
            )

        except (ValueError, TypeError):

            random_percentage = 50


        # ----------------------------------------------------
        # NO 100 MAXIMUM FOR SPACES
        # ----------------------------------------------------

        spaces_after_word = max(
            0,
            spaces_after_word
        )


        random_percentage = max(
            1,
            min(
                random_percentage,
                100
            )
        )


        # ====================================================
        # VALIDATE SELECTION MODE
        # ====================================================

        if selection_mode not in (
            "all",
            "selected",
            "random"
        ):

            selection_mode = "all"


        # ====================================================
        # VALIDATE CHARSET
        # ====================================================

        if charset not in CHARSETS:

            charset = "utf-8"


        # ====================================================
        # VALIDATE METHOD
        # ====================================================

        if method not in METHODS:

            method = "q"


        # ====================================================
        # ENCODE
        # ====================================================

        try:

            processed_text = (
                add_spaces_after_words(
                    text,
                    spaces_after_word
                )
            )


            # =================================================
            # MODE 1
            #
            # Entire sentence
            #
            # Q encoding becomes ONE SINGLE BLOCK.
            # =================================================

            if selection_mode == "all":

                result = encode_text(
                    processed_text,
                    charset,
                    method,
                    space_hex
                )


            # =================================================
            # MODE 2
            # =================================================

            elif selection_mode == "selected":

                result = encode_selected_items(
                    processed_text,
                    selected_items,
                    charset,
                    method,
                    space_hex
                )


            # =================================================
            # MODE 3
            # =================================================

            elif selection_mode == "random":

                result = encode_random_selected_items(
                    processed_text,
                    selected_items,
                    charset,
                    method,
                    space_hex,
                    random_percentage
                )


            # ------------------------------------------------
            # SINGLE LINE
            # ------------------------------------------------

            if single_line and result is not None:

                result = (
                    result
                    .replace("\r", "")
                    .replace("\n", "")
                )


        except UnicodeEncodeError:

            error = (
                "The selected character encoding "
                "cannot represent one or more "
                "characters in the input."
            )

            result = None


        except LookupError:

            error = (
                "The selected character encoding "
                "is not supported."
            )

            result = None


        except Exception as exc:

            error = str(exc)

            result = None


    # ========================================================
    # RENDER PAGE
    # ========================================================

    return render_template_string(

        HTML,

        text=text,

        charset=charset,

        method=method,

        selection_mode=selection_mode,

        selected_items=selected_items,

        spaces_after_word=spaces_after_word,

        space_hex=space_hex,

        single_line=single_line,

        random_percentage=random_percentage,

        result=result,

        error=error,

        charsets=CHARSETS,

        methods=METHODS,

        charset_name=CHARSETS.get(
            charset,
            charset
        ),

        method_name=METHODS.get(
            method,
            method
        ),

        output_length=(
            len(result)
            if result is not None
            else 0
        )

    )


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
