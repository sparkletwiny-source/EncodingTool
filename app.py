from flask import Flask, request, render_template_string
import base64
import html
import json
import urllib.parse
import re
import random


app = Flask(__name__)


# ============================================================
# CHARACTER SETS
# ============================================================

CHARSETS = {
    "utf-8": "UTF-8",
    "utf-16-le": "UTF-16 LE",
    "utf-16-be": "UTF-16 BE",
    "utf-32-le": "UTF-32 LE",
    "utf-32-be": "UTF-32 BE",
    "ascii": "ASCII",
    "iso-8859-1": "ISO-8859-1 / Latin-1",
    "iso-8859-2": "ISO-8859-2",
    "iso-8859-7": "ISO-8859-7",
    "cp1252": "Windows-1252",
    "cp1251": "Windows-1251",
    "shift_jis": "Shift_JIS",
    "euc_jp": "EUC-JP",
    "gb2312": "GB2312",
    "gbk": "GBK",
    "gb18030": "GB18030",
    "big5": "Big5",
    "euc_kr": "EUC-KR",
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


CODECS = {
    key: key
    for key in CHARSETS
}


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
# QUOTED PRINTABLE
# ============================================================

def q_encode_bytes(data, space_hex=False):

    result = []

    for b in data:

        if b == 0x20:

            if space_hex:
                result.append("=20")
            else:
                result.append("_")

        else:

            result.append(
                f"={b:02X}"
            )

    return "".join(result)


def encode_q(
    text,
    charset,
    space_hex=False
):

    data = text.encode(
        CODECS[charset]
    )

    encoded = q_encode_bytes(
        data,
        space_hex
    )

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
            text,
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


# ============================================================
# MAIN ENCODER
# ============================================================

def encode_text(
    text,
    charset,
    method,
    space_hex
):

    if method == "q":

        return encode_q(
            text,
            charset,
            space_hex
        )

    if method == "base64":

        return encode_base64(
            text,
            charset
        )

    return encode_other(
        text,
        charset,
        method
    )


# ============================================================
# ENCODE SELECTED ITEMS
#
# Normal selected mode:
# Every matching selected item is encoded.
# ============================================================

def encode_selected_items(
    text,
    selected_items,
    charset,
    method,
    space_hex
):

    if not selected_items.strip():

        return text

    items = [
        x.strip()
        for x in selected_items.split(",")
        if x.strip()
    ]

    if not items:

        return text

    # Longest items first.
    items.sort(
        key=len,
        reverse=True
    )

    pattern = "|".join(
        re.escape(item)
        for item in items
    )

    regex = re.compile(
        pattern
    )

    def replacement(match):

        value = match.group(0)

        return encode_text(
            value,
            charset,
            method,
            space_hex
        )

    return regex.sub(
        replacement,
        text
    )


# ============================================================
# RANDOMLY ENCODE SELECTED ITEMS
#
# If selected_items contains values:
#     Clean,Today,!,@
#
# only random occurrences of those values are encoded.
#
# If selected_items is empty:
# automatically finds words in the complete sentence and
# randomly encodes some of them.
#
# A new random decision is made on EVERY Encode click.
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
    # LIMIT RANDOM PERCENTAGE
    # --------------------------------------------------------

    random_percentage = max(
        1,
        min(
            random_percentage,
            100
        )
    )


    # ========================================================
    # CASE 1
    # SPECIFIC ITEMS WERE ENTERED
    # ========================================================

    if selected_items.strip():

        items = [
            x.strip()
            for x in selected_items.split(",")
            if x.strip()
        ]

        if not items:

            return text

        # Longest first so that multi-character items are
        # matched before shorter items.
        items.sort(
            key=len,
            reverse=True
        )

        pattern = "|".join(
            re.escape(item)
            for item in items
        )

        regex = re.compile(
            pattern
        )

        def replacement(match):

            value = match.group(0)

            # New random number for every occurrence.
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

        return regex.sub(
            replacement,
            text
        )


    # ========================================================
    # CASE 2
    # NO SPECIFIC ITEMS
    #
    # Automatically find words in the entire sentence.
    # ========================================================

    word_pattern = r"\b[\w]+\b"

    def random_word_replacement(match):

        value = match.group(0)

        # Do not encode one-character words automatically.
        if len(value) <= 1:

            return value

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

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Email Encoding Tool</title>


<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

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

    padding: 24px;

    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    color: #e8eefc;

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(59, 130, 246, 0.30),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 15%,
            rgba(139, 92, 246, 0.28),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(14, 165, 233, 0.20),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #020617 0%,
            #0b172a 50%,
            #111827 100%
        );

    background-attachment: fixed;

    transition:
        background 0.3s ease,
        color 0.3s ease;
}


/* ==========================================================
   MAIN CONTAINER
   ========================================================== */

.container {

    width: 100%;

    max-width: 1400px;

    min-height:
        calc(100vh - 48px);

    margin: 0 auto;

    padding: 30px;

    border:
        1px solid
        rgba(148, 163, 184, 0.20);

    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            rgba(15, 23, 42, 0.96),
            rgba(17, 24, 39, 0.92)
        );

    box-shadow:
        0 25px 70px
        rgba(0, 0, 0, 0.45),

        inset 0 1px 0
        rgba(255, 255, 255, 0.06);

    backdrop-filter:
        blur(18px);

    -webkit-backdrop-filter:
        blur(18px);
}


/* ==========================================================
   HEADER
   ========================================================== */

.header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    margin-bottom: 25px;
}

h1 {

    margin: 0;

    font-size: 30px;

    font-weight: 700;

    letter-spacing: -0.5px;

    background:
        linear-gradient(
            90deg,
            #60a5fa,
            #a78bfa,
            #22d3ee
        );

    -webkit-background-clip: text;

    background-clip: text;

    color: transparent;
}


/* ==========================================================
   TWO COLUMN LAYOUT
   ========================================================== */

.main-grid {

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        minmax(0, 1fr);

    gap: 26px;

    align-items: start;
}

.left-panel,
.right-panel {

    min-width: 0;
}


/* ==========================================================
   LABELS
   ========================================================== */

label {

    display: block;

    font-weight: 600;

    margin-top: 18px;

    margin-bottom: 7px;

    color: #dbeafe;

    font-size: 14px;
}


/* ==========================================================
   INPUTS
   ========================================================== */

textarea,
select,
input[type="number"],
input[type="text"] {

    width: 100%;

    padding: 12px 13px;

    border:
        1px solid #334155;

    border-radius: 9px;

    font-size: 14px;

    background:
        rgba(15, 23, 42, 0.85);

    color: #f8fafc;

    outline: none;

    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        background 0.2s ease;
}

textarea {

    min-height: 160px;

    resize: vertical;

    line-height: 1.5;
}

textarea:focus,
select:focus,
input[type="number"]:focus,
input[type="text"]:focus {

    border-color: #60a5fa;

    background:
        rgba(15, 23, 42, 0.98);

    box-shadow:
        0 0 0 3px
        rgba(59, 130, 246, 0.14),

        0 0 20px
        rgba(59, 130, 246, 0.08);
}

select option {

    background: #111827;

    color: #f8fafc;
}

input[type="radio"],
input[type="checkbox"] {

    margin-right: 7px;

    accent-color: #6366f1;
}


/* ==========================================================
   BOX
   ========================================================== */

.box {

    margin-top: 20px;

    padding: 17px;

    border:
        1px solid
        rgba(96, 165, 250, 0.14);

    border-radius: 11px;

    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.75),
            rgba(15, 23, 42, 0.65)
        );

    box-shadow:
        inset 0 1px 0
        rgba(255, 255, 255, 0.03);
}

.option {

    margin: 10px 0;

    color: #cbd5e1;
}

.option label {

    display: inline;

    margin: 0;

    font-weight: normal;

    color: #cbd5e1;
}


/* ==========================================================
   RANDOM SETTINGS
   ========================================================== */

.random-settings {

    margin-top: 12px;

    padding: 12px;

    border-radius: 9px;

    border:
        1px dashed
        rgba(167, 139, 250, 0.35);

    background:
        rgba(76, 29, 149, 0.12);
}


/* ==========================================================
   BUTTONS
   ========================================================== */

button {

    margin-top: 20px;

    padding: 12px 24px;

    border: 0;

    border-radius: 9px;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );

    color: white;

    cursor: pointer;

    font-size: 14px;

    font-weight: 700;

    box-shadow:
        0 8px 20px
        rgba(37, 99, 235, 0.25);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        opacity 0.2s ease;
}

button:hover {

    opacity: 0.95;

    transform:
        translateY(-1px);

    box-shadow:
        0 12px 28px
        rgba(37, 99, 235, 0.35);
}

button:active {

    transform:
        translateY(0);
}

.copy {

    margin: 0;

    padding:
        9px 16px;

    background:
        linear-gradient(
            135deg,
            #475569,
            #334155
        );

    box-shadow:
        0 6px 16px
        rgba(0, 0, 0, 0.20);
}


/* ==========================================================
   RESULT HEADER
   ========================================================== */

.result-header {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;

    margin-bottom: 7px;
}

.result-header label {

    margin: 0;
}


/* ==========================================================
   RESULT
   ========================================================== */

pre {

    white-space: pre-wrap;

    word-break: break-all;

    background:
        linear-gradient(
            135deg,
            rgba(2, 6, 23, 0.95),
            rgba(15, 23, 42, 0.95)
        );

    padding: 16px;

    border:
        1px solid #334155;

    border-radius: 9px;

    min-height: 180px;

    max-height: 65vh;

    overflow-y: auto;

    color: #86efac;

    font-family:
        Consolas,
        "Courier New",
        monospace;

    font-size: 13px;

    line-height: 1.55;

    margin: 0;
}


/* ==========================================================
   HELP
   ========================================================== */

.help {

    color: #94a3b8;

    font-size: 12px;

    margin-top: 5px;

    line-height: 1.5;
}


/* ==========================================================
   ERROR
   ========================================================== */

.error {

    margin-top: 15px;

    padding: 12px;

    background:
        rgba(127, 29, 29, 0.35);

    color: #fecaca;

    border:
        1px solid
        rgba(248, 113, 113, 0.25);

    border-radius: 8px;
}


/* ==========================================================
   THEME BUTTON
   ========================================================== */

.theme-toggle {

    position: fixed;

    top: 18px;

    right: 20px;

    z-index: 9999;

    margin: 0;

    padding: 9px 16px;

    width: auto;

    border:
        1px solid
        rgba(148, 163, 184, 0.3);

    border-radius: 20px;

    background:
        rgba(15, 23, 42, 0.90);

    color: #f8fafc;

    backdrop-filter:
        blur(10px);

    box-shadow:
        0 8px 25px
        rgba(0, 0, 0, 0.25);

    font-size: 12px;

    cursor: pointer;
}

.theme-toggle:hover {

    transform: none;
}


/* ==========================================================
   LIGHT MODE
   ========================================================== */

body.light-mode {

    color: #172033;

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(59, 130, 246, 0.18),
            transparent 30%
        ),

        radial-gradient(
            circle at 90% 15%,
            rgba(139, 92, 246, 0.16),
            transparent 30%
        ),

        linear-gradient(
            135deg,
            #eef5ff,
            #f8fafc,
            #eef2ff
        );
}

body.light-mode .container {

    background:
        rgba(255, 255, 255, 0.92);

    border-color:
        rgba(100, 116, 139, 0.20);

    box-shadow:
        0 25px 70px
        rgba(15, 23, 42, 0.15);
}

body.light-mode label {

    color: #1e293b;
}

body.light-mode textarea,
body.light-mode select,
body.light-mode input[type="number"],
body.light-mode input[type="text"] {

    background: #ffffff;

    color: #172033;

    border-color: #cbd5e1;
}

body.light-mode select option {

    background: #ffffff;

    color: #172033;
}

body.light-mode .box {

    background:
        linear-gradient(
            135deg,
            #f1f5f9,
            #f8fafc
        );

    border-color: #e2e8f0;
}

body.light-mode .option,
body.light-mode .option label {

    color: #475569;
}

body.light-mode .help {

    color: #64748b;
}

body.light-mode pre {

    background:
        linear-gradient(
            135deg,
            #f8fafc,
            #eef2ff
        );

    color: #166534;

    border-color: #cbd5e1;
}

body.light-mode .random-settings {

    background:
        rgba(245, 243, 255, 0.8);

    border-color:
        rgba(124, 58, 237, 0.25);
}

body.light-mode .theme-toggle {

    background: #ffffff;

    color: #172033;

    border-color: #cbd5e1;

    box-shadow:
        0 6px 20px
        rgba(15, 23, 42, 0.12);
}

body.light-mode .error {

    background: #fff1f2;

    color: #9f1239;

    border-color: #fecdd3;
}


/* ==========================================================
   SCROLLBAR
   ========================================================== */

::-webkit-scrollbar {

    width: 8px;

    height: 8px;
}

::-webkit-scrollbar-track {

    background:
        rgba(15, 23, 42, 0.5);
}

::-webkit-scrollbar-thumb {

    background: #475569;

    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {

    background: #64748b;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 850px) {

    body {

        padding: 10px;
    }

    .container {

        min-height:
            calc(100vh - 20px);

        padding: 20px;

        border-radius: 14px;
    }

    .main-grid {

        grid-template-columns: 1fr;
    }

    h1 {

        font-size: 23px;
    }

    .theme-toggle {

        top: 10px;

        right: 10px;
    }

    button {

        width: 100%;
    }

    .copy {

        width: auto;
    }

    .result-header {

        align-items: stretch;

        flex-direction: column;
    }
}

</style>

</head>


<body>


<!-- ========================================================
     THEME TOGGLE
     ======================================================== -->

<button
    type="button"
    id="themeToggle"
    class="theme-toggle"
    onclick="toggleTheme()"
>
☀️ Light Mode
</button>


<div class="container">


<div class="header">

    <h1>
        Email Encoding Tool
    </h1>

</div>


<div class="main-grid">


<!-- ========================================================
     LEFT SIDE - INPUTS
     ======================================================== -->

<div class="left-panel">


<form method="POST">


<label>
Input sentence
</label>

<textarea
    name="text"
    placeholder="Example: Clean Fridge Today!"
>{{ text }}</textarea>


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


<!-- ========================================================
     ENCODING SELECTION
     ======================================================== -->

<div class="box">

<strong>
Encoding selection
</strong>


<!-- ======================================================
     OPTION 1 - ENTIRE SENTENCE
     ====================================================== -->

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


<!-- ======================================================
     OPTION 2 - SPECIFIC ITEMS
     ====================================================== -->

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


<!-- ======================================================
     OPTION 3 - RANDOM
     ====================================================== -->

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

Random mode creates a new random selection every
time you click Encode.

If specific items are entered, only those items
are randomly encoded.

If the specific-items field is empty, words from
the complete sentence are automatically selected.

</div>


<!-- ======================================================
     RANDOM PERCENTAGE
     ====================================================== -->

<div
    class="random-settings"
    id="randomSettings"
>

<label
    for="random_percentage"
    style="margin-top:0;"
>
Random encoding percentage
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

Example: 30 = approximately 30% of matching
items will be encoded.

100 = encode every matching item.

</div>

</div>

</div>


<!-- ========================================================
     SELECTED ITEMS
     ======================================================== -->

<label>
Specific words / letters / special characters
</label>

<input
    type="text"
    name="selected_items"

    value="{{ selected_items }}"

    placeholder="Example: Clean,Today,!,@,#"
>

<div class="help">

Separate multiple items with commas.

Example:
Clean,Today,!,@,#

For Random mode, these items are randomly
encoded throughout the sentence.

</div>


<!-- ========================================================
     SPACES
     ======================================================== -->

<label>
Spaces after each word
</label>

<input
    type="number"
    name="spaces_after_word"

    min="0"
    max="100"

    value="{{ spaces_after_word }}"
>

<div class="help">

Set to 0 if you do not want additional spaces.

</div>


<!-- ========================================================
     OPTIONS
     ======================================================== -->

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

Encode space as =20 (hex)
instead of _

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


<!-- ========================================================
     WORD LENGTH
     ======================================================== -->

<label>
Encoded Word Length
</label>

<input
    type="number"
    name="word_length"

    min="10"
    max="998"

    value="{{ word_length }}"
>

<div class="help">

Maximum encoded word length setting.

</div>


<!-- ========================================================
     ENCODE BUTTON
     ======================================================== -->

<button type="submit">
Encode
</button>


</form>


</div>


<!-- ========================================================
     RIGHT SIDE - RESULT
     ======================================================== -->

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


<!-- ========================================================
     JAVASCRIPT
     ======================================================== -->

<script>


/* ==========================================================
   COPY RESULT
   ========================================================== */

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


/* ==========================================================
   FALLBACK COPY
   ========================================================== */

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

        document.execCommand(
            "copy"
        );

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


/* ==========================================================
   COPY BUTTON STATUS
   ========================================================== */

function showCopyStatus() {

    const buttons =
        document.querySelectorAll(
            ".copy"
        );

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


/* ==========================================================
   DARK / LIGHT THEME
   ========================================================== */

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


/* ==========================================================
   LOAD SAVED THEME
   ========================================================== */

(function () {

    const savedTheme =
        localStorage.getItem(
            "theme"
        );

    const button =
        document.getElementById(
            "themeToggle"
        );


    if (
        savedTheme === "light"
    ) {

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


/* ==========================================================
   RANDOM SETTINGS UI
   ==========================================================
   
   Random settings remain visible because they are useful
   for the random mode. The radio buttons control the actual
   encoding mode on the server.
   ========================================================== */

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

    word_length = 75

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

        except ValueError:

            spaces_after_word = 0


        # ----------------------------------------------------
        # WORD LENGTH
        # ----------------------------------------------------

        try:

            word_length = int(
                request.form.get(
                    "word_length",
                    "75"
                )
            )

        except ValueError:

            word_length = 75


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

        except ValueError:

            random_percentage = 50


        # ----------------------------------------------------
        # LIMIT VALUES
        # ----------------------------------------------------

        spaces_after_word = max(
            0,
            min(
                spaces_after_word,
                100
            )
        )


        word_length = max(
            10,
            min(
                word_length,
                998
            )
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

            # ------------------------------------------------
            # ADD SPACES
            # ------------------------------------------------

            processed_text = (
                add_spaces_after_words(
                    text,
                    spaces_after_word
                )
            )


            # =================================================
            # MODE 1
            # ENCODE ENTIRE SENTENCE
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
            # ENCODE SPECIFIC ITEMS
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
            # RANDOM ENCODING
            #
            # IMPORTANT:
            # This is now a radio selection and therefore
            # cannot be active together with "all" or
            # "selected".
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

            if single_line:

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

        word_length=word_length,

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

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )
