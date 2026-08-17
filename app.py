from flask import Flask, request, render_template_string
import base64
import codecs
import html
import json
import quopri
import urllib.parse

app = Flask(__name__)

CHARSETS = [
    "UTF-8",
    "UTF-16 LE",
    "UTF-16 BE",
    "UTF-32 LE",
    "UTF-32 BE",
    "ASCII",
    "ISO-8859-1",
    "ISO-8859-2",
    "ISO-8859-7",
    "Windows-1252",
    "Windows-1251",
    "Shift_JIS",
    "EUC-JP",
    "GB2312",
    "GBK",
    "GB18030",
    "Big5",
    "EUC-KR",
]

FORMATS = [
    "RFC 2047 Q",
    "Base64",
    "Quoted-Printable",
    "URL / Percent",
    "HTML Entity",
    "Hexadecimal",
    "Unicode Escape",
    "JSON Unicode Escape",
    "Punycode",
]


def normalize_charset(name):
    aliases = {
        "UTF-8": "utf-8",
        "UTF-16 LE": "utf-16-le",
        "UTF-16 BE": "utf-16-be",
        "UTF-32 LE": "utf-32-le",
        "UTF-32 BE": "utf-32-be",
        "ASCII": "ascii",
        "ISO-8859-1": "iso-8859-1",
        "ISO-8859-2": "iso-8859-2",
        "ISO-8859-7": "iso-8859-7",
        "Windows-1252": "cp1252",
        "Windows-1251": "cp1251",
        "Shift_JIS": "shift_jis",
        "EUC-JP": "euc_jp",
        "GB2312": "gb2312",
        "GBK": "gbk",
        "GB18030": "gb18030",
        "Big5": "big5",
        "EUC-KR": "euc_kr",
    }
    return aliases.get(name, "utf-8")


def q_encode_character(ch, charset, encode_space):
    """
    RFC-2047-style Q encoding.

    Printable ASCII letters/numbers and selected punctuation remain readable.
    Other bytes become =XX.
    Spaces can be represented as _ or =20.
    """
    try:
        data = ch.encode(charset)
    except (UnicodeEncodeError, LookupError):
        data = ch.encode("utf-8")

    result = []

    for byte in data:
        char = chr(byte)

        if byte == 0x20:
            result.append("=20" if encode_space else "_")
        elif (
            33 <= byte <= 126
            and char not in "=?_"
        ):
            result.append(char)
        else:
            result.append(f"={byte:02X}")

    return "".join(result)


def rfc2047_q(text, charset, encode_space):
    encoded = "".join(
        q_encode_character(ch, charset, encode_space)
        for ch in text
    )

    return f"=?{charset}?Q?{encoded}?="


def encode_base64(text, charset):
    try:
        raw = text.encode(charset)
    except UnicodeEncodeError:
        raw = text.encode("utf-8")

    return base64.b64encode(raw).decode("ascii")


def encode_quoted_printable(text, charset, encode_space):
    try:
        raw = text.encode(charset)
    except UnicodeEncodeError:
        raw = text.encode("utf-8")

    result = []

    for byte in raw:
        if byte == 0x20 and encode_space:
            result.append("=20")
        elif 33 <= byte <= 126 and byte != 61:
            result.append(chr(byte))
        elif byte == 0x20:
            result.append(" ")
        else:
            result.append(f"={byte:02X}")

    return "".join(result)


def encode_text(text, charset, fmt, encode_space=False):
    if not text:
        return ""

    if fmt == "RFC 2047 Q":
        return rfc2047_q(text, charset, encode_space)

    if fmt == "Base64":
        return encode_base64(text, charset)

    if fmt == "Quoted-Printable":
        return encode_quoted_printable(text, charset, encode_space)

    if fmt == "URL / Percent":
        return urllib.parse.quote(text, safe="")

    if fmt == "HTML Entity":
        return html.escape(text, quote=True)

    if fmt == "Hexadecimal":
        try:
            raw = text.encode(charset)
        except UnicodeEncodeError:
            raw = text.encode("utf-8")

        return "".join(f"{b:02X}" for b in raw)

    if fmt == "Unicode Escape":
        return "".join(f"\\u{ord(ch):04X}" for ch in text)

    if fmt == "JSON Unicode Escape":
        return json.dumps(text, ensure_ascii=True)[1:-1]

    if fmt == "Punycode":
        try:
            return text.encode("punycode").decode("ascii")
        except Exception:
            return text

    return text


def apply_selected_encoding(
    text,
    selected_items,
    charset,
    fmt,
    encode_space=False,
    spaces_after_word=0
):
    """
    Encode only selected words/characters.

    Example:
        text = "Clean Fridge Today!"
        selected = ["Clean", "Today", "!"]

    The unselected text remains unchanged.
    """

    if not selected_items:
        return encode_text(
            text,
            charset,
            fmt,
            encode_space
        )

    # Longer selections first prevents partial matches.
    selected_items = sorted(
        [x for x in selected_items if x],
        key=len,
        reverse=True
    )

    result = []
    i = 0

    while i < len(text):
        matched = None

        for item in selected_items:
            if text.startswith(item, i):
                matched = item
                break

        if matched is not None:
            encoded = encode_text(
                matched,
                charset,
                fmt,
                encode_space
            )

            result.append(encoded)

            if spaces_after_word > 0:
                # Add the requested number of spaces after
                # each selected word.
                if fmt == "RFC 2047 Q":
                    if encode_space:
                        result.append("=20" * spaces_after_word)
                    else:
                        result.append("_" * spaces_after_word)
                else:
                    result.append(" " * spaces_after_word)

            i += len(matched)

        else:
            result.append(text[i])
            i += 1

    return "".join(result)


PAGE = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Encoding Tool</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    font-family: Arial, Helvetica, sans-serif;

    background:
        radial-gradient(
            circle at 15% 20%,
            rgba(99,102,241,.30),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 25%,
            rgba(14,165,233,.25),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 90%,
            rgba(168,85,247,.20),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #0f172a,
            #111827 45%,
            #1e1b4b
        );

    background-attachment: fixed;
    color: #e5e7eb;

    transition:
        background .35s ease,
        color .35s ease;
}

body::before {
    content: "";
    position: fixed;

    width: 400px;
    height: 400px;

    left: -150px;
    top: -150px;

    background:
        radial-gradient(
            circle,
            rgba(59,130,246,.25),
            transparent 70%
        );

    filter: blur(30px);

    animation:
        floatingGlow 8s
        ease-in-out
        infinite
        alternate;

    pointer-events: none;
    z-index: -1;
}

@keyframes floatingGlow {

    from {
        transform:
            translate(0,0)
            scale(1);
    }

    to {
        transform:
            translate(180px,120px)
            scale(1.25);
    }
}

.container {

    width: min(950px, 92%);
    margin: 45px auto;

    padding: 30px;

    background:
        rgba(255,255,255,.08);

    border:
        1px solid
        rgba(255,255,255,.15);

    border-radius: 22px;

    backdrop-filter:
        blur(18px);

    -webkit-backdrop-filter:
        blur(18px);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,.35),

        inset 0 1px 0
        rgba(255,255,255,.08);

    transition:
        background .35s ease,
        border .35s ease;
}

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
}

.subtitle {
    margin-top: 6px;
    color: #a5b4fc;
    font-size: 14px;
}

.theme-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
}

.theme-toggle button {
    padding: 9px 15px;
    border: 0;
    border-radius: 10px;
    cursor: pointer;

    background: #ffffff;
    color: #111827;

    font-size: 14px;

    transition:
        transform .2s,
        background .2s;
}

.theme-toggle button:hover {
    transform: translateY(-2px);
}

label {
    display: block;
    margin: 18px 0 8px;
    font-weight: bold;
    font-size: 14px;
}

textarea,
input,
select {

    width: 100%;

    padding: 12px 14px;

    border-radius: 11px;

    border:
        1px solid
        rgba(255,255,255,.16);

    background:
        rgba(0,0,0,.20);

    color: #ffffff;

    outline: none;

    font-size: 14px;

    transition:
        border .2s,
        box-shadow .2s;
}

textarea {
    min-height: 130px;
    resize: vertical;
}

textarea:focus,
input:focus,
select:focus {

    border-color:
        #818cf8;

    box-shadow:
        0 0 0 3px
        rgba(129,140,248,.15);
}

select option {
    background: #111827;
    color: white;
}

.row {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 18px;
}

.options {

    margin-top: 20px;

    padding: 18px;

    border-radius: 15px;

    background:
        rgba(0,0,0,.12);

    border:
        1px solid
        rgba(255,255,255,.08);
}

.radio-row {

    display: flex;

    flex-wrap: wrap;

    gap: 18px;

    margin-top: 10px;
}

.radio-row label {

    margin: 0;

    display: flex;

    align-items: center;

    gap: 7px;

    font-weight: normal;
}

.radio-row input {
    width: auto;
}

.checkbox {

    display: flex;

    align-items: center;

    gap: 8px;

    margin-top: 14px;
}

.checkbox input {
    width: auto;
}

button.encode {

    width: 100%;

    margin-top: 25px;

    padding: 14px;

    border: 0;

    border-radius: 12px;

    cursor: pointer;

    font-size: 16px;

    font-weight: bold;

    color: white;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #8b5cf6
        );

    box-shadow:
        0 10px 25px
        rgba(99,102,241,.25);

    transition:
        transform .2s,
        box-shadow .2s;
}

button.encode:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 14px 30px
        rgba(99,102,241,.35);
}

.result {

    margin-top: 25px;
}

.result textarea {
    min-height: 160px;
}

.copy-button {

    margin-top: 10px;

    padding: 10px 18px;

    border: 0;

    border-radius: 10px;

    cursor: pointer;

    background: #22c55e;

    color: white;

    font-weight: bold;
}

.stats {

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 12px;

    margin-top: 15px;
}

.stat {

    padding: 14px;

    border-radius: 12px;

    background:
        rgba(255,255,255,.06);

    border:
        1px solid
        rgba(255,255,255,.08);
}

.stat-title {

    font-size: 12px;

    color: #94a3b8;

    margin-bottom: 5px;
}

.stat-value {

    font-size: 14px;

    font-weight: bold;

    word-break: break-word;
}


/* WHITE MODE */

body.light-mode {

    background:
        radial-gradient(
            circle at 15% 20%,
            rgba(99,102,241,.12),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 25%,
            rgba(14,165,233,.10),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #f8fafc,
            #eef2ff,
            #f0f9ff
        );

    color: #111827;
}

body.light-mode .container {

    background:
        rgba(255,255,255,.82);

    border:
        1px solid
        rgba(0,0,0,.08);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,.10);
}

body.light-mode textarea,
body.light-mode input,
body.light-mode select {

    background:
        rgba(255,255,255,.9);

    color: #111827;

    border-color:
        rgba(0,0,0,.12);
}

body.light-mode select option {

    background: white;
    color: #111827;
}

body.light-mode .options {

    background:
        rgba(0,0,0,.035);

    border-color:
        rgba(0,0,0,.07);
}

body.light-mode .subtitle {
    color: #4f46e5;
}

body.light-mode .stat {

    background:
        rgba(0,0,0,.035);

    border-color:
        rgba(0,0,0,.07);
}

body.light-mode .stat-title {
    color: #64748b;
}

body.light-mode .theme-toggle button {

    background: #111827;
    color: white;
}


/* MOBILE */

@media (max-width: 700px) {

    .container {
        padding: 20px;
        margin: 20px auto;
    }

    .header {
        flex-direction: column;
        align-items: flex-start;
    }

    .row {
        grid-template-columns: 1fr;
    }

    .stats {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 24px;
    }
}

</style>

</head>


<body>

<div class="container">

    <div class="header">

        <div>

            <h1>Encoding Tool</h1>

            <div class="subtitle">
                Character and text encoding utility
            </div>

        </div>

        <div class="theme-toggle">

            <span id="themeLabel">
                Dark Mode
            </span>

            <button
                type="button"
                id="themeButton"
                onclick="toggleTheme()">

                ☀️ White Mode

            </button>

        </div>

    </div>


    <form method="POST">

        <label>
            Input Text
        </label>

        <textarea
            name="text"
            placeholder="Enter your sentence here..."
            required>{{ text }}</textarea>


        <div class="row">

            <div>

                <label>
                    Character Encoding
                </label>

                <select name="charset">

                    {% for c in charsets %}

                    <option
                        value="{{ c }}"
                        {% if charset == c %}
                        selected
                        {% endif %}>

                        {{ c }}

                    </option>

                    {% endfor %}

                </select>

            </div>


            <div>

                <label>
                    Encoding Format
                </label>

                <select name="format">

                    {% for f in formats %}

                    <option
                        value="{{ f }}"
                        {% if fmt == f %}
                        selected
                        {% endif %}>

                        {{ f }}

                    </option>

                    {% endfor %}

                </select>

            </div>

        </div>


        <div class="options">

            <label>
                Encoding Selection
            </label>

            <div class="radio-row">

                <label>

                    <input
                        type="radio"
                        name="mode"
                        value="entire"
                        {% if mode != "specific" %}
                        checked
                        {% endif %}>

                    Encode entire sentence

                </label>


                <label>

                    <input
                        type="radio"
                        name="mode"
                        value="specific"
                        {% if mode == "specific" %}
                        checked
                        {% endif %}>

                    Encode specific words / letters / characters

                </label>

            </div>


            <label>
                Specific words / letters / special characters
            </label>

            <input
                type="text"
                name="specific"
                value="{{ specific }}"
                placeholder="Example: Clean,Today,!,@,#">

            <small>
                Separate multiple items with commas.
            </small>


            <label>
                Spaces after each word
            </label>

            <input
                type="number"
                name="spaces"
                min="0"
                value="{{ spaces }}">


            <div class="checkbox">

                <input
                    type="checkbox"
                    id="encodeSpace"
                    name="encode_space"
                    {% if encode_space %}
                    checked
                    {% endif %}>

                <label
                    for="encodeSpace"
                    style="margin:0;font-weight:normal;">

                    Encode space as =20 (hex) instead of _

                </label>

            </div>


            <div class="checkbox">

                <input
                    type="checkbox"
                    id="singleLine"
                    name="single_line"
                    {% if single_line %}
                    checked
                    {% endif %}>

                <label
                    for="singleLine"
                    style="margin:0;font-weight:normal;">

                    Single line output

                </label>

            </div>

        </div>


        <button
            class="encode"
            type="submit">

            Encode

        </button>

    </form>


    {% if result %}

    <div class="result">

        <label>
            Result
        </label>

        <textarea
            id="result"
            readonly>{{ result }}</textarea>


        <button
            class="copy-button"
            type="button"
            onclick="copyResult()">

            📋 Copy Result

        </button>


        <div class="stats">

            <div class="stat">

                <div class="stat-title">
                    Character Encoding
                </div>

                <div class="stat-value">
                    {{ charset }}
                </div>

            </div>


            <div class="stat">

                <div class="stat-title">
                    Encoding Format
                </div>

                <div class="stat-value">
                    {{ fmt }}
                </div>

            </div>


            <div class="stat">

                <div class="stat-title">
                    Output Length
                </div>

                <div class="stat-value">
                    {{ result|length }}
                </div>

            </div>

        </div>

    </div>

    {% endif %}

</div>


<script>

function toggleTheme() {

    const body =
        document.body;

    const button =
        document.getElementById(
            "themeButton"
        );

    const label =
        document.getElementById(
            "themeLabel"
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

        label.innerHTML =
            "White Mode";

        localStorage.setItem(
            "theme",
            "light"
        );

    } else {

        button.innerHTML =
            "☀️ White Mode";

        label.innerHTML =
            "Dark Mode";

        localStorage.setItem(
            "theme",
            "dark"
        );
    }
}


window.addEventListener(
    "DOMContentLoaded",
    function () {

        const savedTheme =
            localStorage.getItem(
                "theme"
            );

        if (
            savedTheme === "light"
        ) {

            document.body.classList.add(
                "light-mode"
            );

            document.getElementById(
                "themeButton"
            ).innerHTML =
                "🌙 Dark Mode";

            document.getElementById(
                "themeLabel"
            ).innerHTML =
                "White Mode";
        }
    }
);


function copyResult() {

    const result =
        document.getElementById(
            "result"
        );

    navigator.clipboard.writeText(
        result.value
    ).then(function () {

        const button =
            document.querySelector(
                ".copy-button"
            );

        const original =
            button.innerHTML;

        button.innerHTML =
            "✓ Copied";

        setTimeout(
            function () {
                button.innerHTML =
                    original;
            },
            1500
        );

    });

}

</script>

</body>

</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():

    text = ""
    charset = "UTF-8"
    fmt = "RFC 2047 Q"
    mode = "entire"
    specific = ""
    spaces = 0
    encode_space = False
    single_line = True
    result = ""

    if request.method == "POST":

        text = request.form.get(
            "text",
            ""
        )

        charset = request.form.get(
            "charset",
            "UTF-8"
        )

        fmt = request.form.get(
            "format",
            "RFC 2047 Q"
        )

        mode = request.form.get(
            "mode",
            "entire"
        )

        specific = request.form.get(
            "specific",
            ""
        )

        try:
            spaces = int(
                request.form.get(
                    "spaces",
                    "0"
                )
            )
        except ValueError:
            spaces = 0

        encode_space = (
            request.form.get(
                "encode_space"
            )
            == "on"
        )

        single_line = (
            request.form.get(
                "single_line"
            )
            == "on"
        )

        if mode == "specific":

            selected_items = [
                item.strip()
                for item in specific.split(",")
                if item.strip()
            ]

            result = apply_selected_encoding(
                text,
                selected_items,
                charset,
                fmt,
                encode_space,
                spaces
            )

        else:

            result = encode_text(
                text,
                charset,
                fmt,
                encode_space
            )

        if single_line:

            result = (
                result
                .replace("\r", "")
                .replace("\n", "")
            )

    return render_template_string(
        PAGE,
        text=text,
        charset=charset,
        fmt=fmt,
        mode=mode,
        specific=specific,
        spaces=spaces,
        encode_space=encode_space,
        single_line=single_line,
        result=result,
        charsets=CHARSETS,
        formats=FORMATS
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
