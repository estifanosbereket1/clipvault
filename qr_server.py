import html
import json
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

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

    formatted_content = f"""<!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>ClipQR</title>
      <style>
        :root {{
          --bg: #0f1115;
          --card: #1a1d24;
          --border: #2a2e37;
          --text: #e8e9ec;
          --muted: #8b8f9a;
          --accent: #5b8cff;
          --success: #34d399;
          --error: #f87171;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          padding: 24px;
        }}
        .card {{
          width: 100%;
          max-width: 420px;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 28px 24px;
        }}
        .label {{
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--muted);
          margin: 0 0 10px;
        }}
        pre {{
          background: #101319;
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 16px;
          color: var(--text);
          font-size: 14px;
          line-height: 1.5;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 240px;
          overflow-y: auto;
          margin: 0 0 20px;
        }}
        #status {{
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--muted);
          margin: 0 0 18px;
        }}
        #status.success {{ color: var(--success); }}
        #status.error {{ color: var(--error); }}
        .dot {{
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--muted);
          flex-shrink: 0;
        }}
        #status.success .dot {{ background: var(--success); }}
        #status.error .dot {{ background: var(--error); }}
        button {{
          width: 100%;
          padding: 13px;
          border-radius: 10px;
          border: none;
          background: var(--accent);
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
        }}
        button:active {{ opacity: 0.85; }}
      </style>
    </head>
    <body>
      <div class="card">
        <p class="label">Clipboard content</p>
        <pre>{safe_content}</pre>
        <p id="status"><span class="dot"></span><span id="status-text">Copying...</span></p>
        <button id="copy-btn" onclick="copyText()">Tap to copy</button>
      </div>
      <script>
        const clipboardText = {js_content};
        const statusEl = document.getElementById("status");
        const statusText = document.getElementById("status-text");

        async function copyText() {{
          try {{
            await navigator.clipboard.writeText(clipboardText);
            statusEl.className = "success";
            statusText.innerText = "Copied to clipboard";
          }} catch (err) {{
            statusEl.className = "error";
            statusText.innerText = "Tap the button below to copy";
          }}
        }}
        copyText();
      </script>
    </body>
    </html>"""
    return HTMLResponse(content=formatted_content)


def get_ca_root_path() -> str:
    result = subprocess.run(["mkcert", "-CAROOT"], capture_output=True, text=True)
    ca_root_dir = result.stdout.strip()
    return f"{ca_root_dir}/rootCA.pem"


@app.get("/setup-ca")
def get_ca_certificate():
    ca_path = get_ca_root_path()
    return FileResponse(
        path=ca_path,
        media_type="application/x-x509-ca-cert",
        filename="clipqr-ca.pem",
    )
