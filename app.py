from flask import Flask, request, render_template_string
import base64
import html
import json
import urllib.parse
import re

app = Flask(__name__)

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
    key: key for key in CHARSETS
}


def add_spaces_after_words(text, count):
    if count <= 0:
        return text

    return re.sub(
        r"(\S+)(?=\s|$)",
        lambda m: m.group(1) + (" " * count),
        text
    )


def q_encode_bytes(data, space_hex=False):
    result = []

    for b in data:
        if b == 0x20:
            result.append("=20" if space_hex else "_")
        else:
            result.append(f"={b:02X}")

    return "".join(result)


def encode_q(text, charset, space_hex=False):
    data = text.encode(CODECS[charset])

    encoded = q_encode_bytes(
        data,
        space_hex
    )

    return (
        f"=?{charset.upper()}?Q?"
        f"{encoded}"
        f"?="
    )


def encode_base64(text, charset):
    data = text.encode(CODECS[charset])

    encoded = base64.b64encode(
        data
    ).decode("ascii")

    return (
        f"=?{charset.upper()}?B?"
        f"{encoded}"
        f"?="
    )


def encode_other(text, charset, method):

    data = text.encode(CODECS[charset])

    if method == "url":
        return urllib.parse.quote(
            text,
            safe=""
        )

    if method == "html":
        return html.escape(text)

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


def encode_selected_items(
    text,
    selected_items,
    charset,
    method,
    space_hex
):
    """
    Encodes only the words/characters entered
    in the selected-items field.

    Items are separated by commas.

    Example:
        Clean,Today,!
    """

    if not selected_items.strip():
        return text

    items = [
        x.strip()
        for x in selected_items.split(",")
        if x.strip()
    ]

    if not items:
        return text

    # Longest first prevents a shorter item
    # from being matched before a longer item.
    items.sort(
        key=len,
        reverse=True
    )

    pattern = "|".join(
        re.escape(item)
        for item in items
    )

    regex = re.compile(pattern)

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

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 30px;
    background: #f2f3f5;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 1000px;
    margin: auto;
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 3px 15px rgba(0,0,0,.12);
}

h1 {
    margin-top: 0;
}

label {
    display: block;
    font-weight: bold;
    margin-top: 18px;
    margin-bottom: 7px;
}

textarea,
select,
input[type="number"],
input[type="text"] {
    width: 100%;
    padding: 11px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 15px;
}

textarea {
    min-height: 140px;
    resize: vertical;
}

input[type="radio"],
input[type="checkbox"] {
    margin-right: 7px;
}

.box {
    margin-top: 20px;
    padding: 17px;
    background: #f7f7f7;
    border-radius: 7px;
}

.option {
    margin: 10px 0;
}

.option label {
    display: inline;
    margin: 0;
    font-weight: normal;
}

button {
    margin-top: 20px;
    padding: 12px 22px;
    border: 0;
    border-radius: 5px;
    background: #222;
    color: white;
    cursor: pointer;
    font-size: 15px;
}

button:hover {
    opacity: .85;
}

.copy {
    background: #555;
    margin-left: 8px;
}

pre {
    white-space: pre-wrap;
    word-break: break-all;
    background: #f1f1f1;
    padding: 16px;
    border: 1px solid #ddd;
    border-radius: 5px;
    min-height: 90px;
}

.help {
    color: #666;
    font-size: 13px;
    margin-top: 5px;
}

.error {
    margin-top: 15px;
    padding: 12px;
    background: #ffe8e8;
    color: #9b0000;
    border-radius: 5px;
}

</style>

</head>


<body>

<div class="container">

<h1>Email Encoding Tool</h1>


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


<div class="box">

<strong>Encoding selection</strong>


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

</div>


<label>
Specific words / letters / special characters
</label>

<input
    type="text"
    name="selected_items"
    value="{{ selected_items }}"
    placeholder="Example: Clean,Today,!"
>

<div class="help">
Separate multiple items with commas.
Example:
Clean,Today,!,@,# 
</div>


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


<button type="submit">
Encode
</button>


</form>


{% if result is not none %}

<label>
Result
</label>

<pre id="result">{{ result }}</pre>

<button
    type="button"
    class="copy"
    onclick="copyResult()"
>
Copy Result
</button>


<div class="box">

<strong>Encoding:</strong>
{{ method_name }}

<br>

<strong>Character set:</strong>
{{ charset_name }}

<br>

<strong>Selection mode:</strong>
{{ selection_mode }}

<br>

<strong>Selected items:</strong>
{{ selected_items if selected_items else "None" }}

<br>

<strong>Spaces after each word:</strong>
{{ spaces_after_word }}

<br>

<strong>Output length:</strong>
{{ output_length }}

</div>

{% endif %}


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


</div>


<script>

function copyResult() {

    const result =
        document.getElementById("result");

    if (!result) {
        return;
    }

    navigator.clipboard
        .writeText(result.innerText)
        .then(function() {

            alert("Result copied!");

        })
        .catch(function() {

            alert("Copy failed.");

        });

}

</script>


</body>

</html>
"""


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

    result = None

    error = None


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


        try:

            spaces_after_word = int(
                request.form.get(
                    "spaces_after_word",
                    "0"
                )
            )

        except ValueError:

            spaces_after_word = 0


        try:

            word_length = int(
                request.form.get(
                    "word_length",
                    "75"
                )
            )

        except ValueError:

            word_length = 75


        spaces_after_word = max(
            0,
            min(
                spaces_after_word,
                100
            )
        )


        try:

            # ------------------------------------------------
            # SELECTIVE MODE
            # ------------------------------------------------

            if selection_mode == "selected":

                # Add requested spaces first.
                processed_text = (
                    add_spaces_after_words(
                        text,
                        spaces_after_word
                    )
                )

                result = encode_selected_items(
                    processed_text,
                    selected_items,
                    charset,
                    method,
                    space_hex
                )


            # ------------------------------------------------
            # ENCODE EVERYTHING
            # ------------------------------------------------

            else:

                processed_text = (
                    add_spaces_after_words(
                        text,
                        spaces_after_word
                    )
                )

                result = encode_text(
                    processed_text,
                    charset,
                    method,
                    space_hex
                )


            # ------------------------------------------------
            # SINGLE LINE
            # ------------------------------------------------

            if single_line:

                result = result.replace(
                    "\r",
                    ""
                ).replace(
                    "\n",
                    ""
                )


        except UnicodeEncodeError:

            error = (
                "The selected character encoding "
                "cannot represent one or more "
                "characters in the input."
            )

        except Exception as exc:

            error = str(exc)


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


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )