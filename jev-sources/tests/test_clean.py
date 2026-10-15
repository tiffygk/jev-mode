import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import clean

WIDGET = 'Intro words stay.\n\nexport function SdkSignature({children}) {\n  return <div className="sig">{children}</div>;\n}\n\nAfter the widget.'
ARROW = 'export const Card = () => (\n<div className="card"/>\n);\n\nImportant prose after the arrow widget.\n\n```js\nfunction f() {\n}\n```\nAfter the fence.'
OPEN = 'export function Broken() {\n  return 1;\n\n## Next heading\n\nReal prose here.'
SHARE = 'Try it in the [playground](https://console.typesafe.ai/playground#share/eJyrVkrLz1eyUkpKLFKqBQApvwVP) now.'
SIG = '<SdkSignature>\n  <span className="n">\n    {"request_id"}\n  </span>\n  <span className="p">\n    {":"}\n  </span>\n  <span className="n">\n    {" str"}\n  </span>\n</SdkSignature>'
IMGS = '<img src="/a-light.png" alt="Fan-out diagram" className="block dark:hidden" />\n<img src="/a-dark.png" alt="Fan-out diagram" className="hidden dark:block" />'
HEAD_DOTTED = '<h3 id="typesafe_sdk.SystemOneResponse.request_id">\n  request\\_id\n</h3>\n\nThe id of the request.'
HEAD_PLAIN = '<h2 id="response">\n  Response\n</h2>'
NOTE = '<Note>\n  Long context is slower and less accurate.\n</Note>\n<Tip>Batch questions in one request.</Tip>\n<Warning>Images are experimental.</Warning>'
FENCED = '```js\nexport function keep() {\n}\n```'


def test_widget_code_goes_and_the_words_stay():
    out = clean.clean(WIDGET)
    assert "export function" not in out and "Intro words stay." in out and "After the widget." in out


def test_arrow_widget_ending_in_paren_semicolon_keeps_what_follows():
    out = clean.clean(ARROW)
    assert "export const" not in out and "Important prose after the arrow widget." in out
    assert "```js\nfunction f() {\n}\n```" in out and "After the fence." in out


def test_unclosed_export_keeps_the_rest_of_the_page():
    out = clean.clean(OPEN)
    assert "## Next heading" in out and "Real prose here." in out


def test_share_link_keeps_the_link_and_its_text():
    out = clean.clean(SHARE)
    assert "#share/" not in out and "https://console.typesafe.ai/playground" in out and "[playground]" in out


def test_signature_becomes_plain_code():
    out = clean.clean(SIG)
    assert "<span" not in out and "request_id: str" in out and out.startswith("```python")


def test_image_pair_becomes_one_alt_text():
    assert clean.clean(IMGS).strip() == "[image: Fan-out diagram]"


def test_dotted_html_heading_takes_its_id():
    out = clean.clean(HEAD_DOTTED)
    assert "### typesafe_sdk.SystemOneResponse.request_id" in out and "<h3" not in out and "The id of the request." in out


def test_plain_html_heading_takes_its_text():
    assert clean.clean(HEAD_PLAIN).strip() == "## Response"


def test_note_tip_warning_print_as_written():
    assert clean.clean(NOTE) == NOTE


def test_code_inside_fences_is_never_touched():
    assert clean.clean(FENCED) == FENCED
    shared = "```\nhttps://console.typesafe.ai/playground#share/abc\n```"
    assert clean.clean(shared) == shared


def test_cleaning_twice_changes_nothing():
    for t in (WIDGET, ARROW, OPEN, SHARE, SIG, IMGS, HEAD_DOTTED, HEAD_PLAIN, NOTE):
        once = clean.clean(t)
        assert clean.clean(once) == once


def test_code_shaped_counts_only_lines_outside_fences():
    assert clean.code_shaped(WIDGET.split("\n") + FENCED.split("\n")) == 3
