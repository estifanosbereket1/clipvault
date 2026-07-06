import html
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from storage import get_entry_by_id

app = FastAPI()


@app.get("/c/{entry_id}")
def get_clipboard_page(entry_id: int):
    entry = get_entry_by_id(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Not found")
    content = entry["content"]
    safe_content = html.escape(content)
    js_content = json.dumps(content)

    formatted_content = f"""<html>
    <body>
      <pre>{safe_content}</pre>
      <p id="status">Copying...</p>
      <button id="copy-btn" onclick="copyText()">Tap to copy</button>
      <script>
        const clipboardText = {js_content}
        async function copyText() {{
        try {{
           await navigator.clipboard.writeText(clipboardText);
           document.getElementById("status").innerText = "Copied to clipboard ✓";
         }} catch (err) {{
         document.getElementById("status").innerText = "Error: " + err.message;
         }}
        }}
        copyText();
      </script>
    </body>
    </html>"""
    return HTMLResponse(content=formatted_content)
