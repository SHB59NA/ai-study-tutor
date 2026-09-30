"""Real browser smoke test; produces screenshots without any model API calls."""
from pathlib import Path
import os
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    env = dict(os.environ, GEMINI_API_KEY="", GOOGLE_API_KEY="", GRADIO_ANALYTICS_ENABLED="False",
               GRADIO_SERVER_NAME="127.0.0.1", GRADIO_SERVER_PORT="7861")
    with (out / "demo-server.log").open("w") as log:
        server = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                                  stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError("Demo process exited; see artifacts/demo-server.log")
                try:
                    urllib.request.urlopen("http://127.0.0.1:7861", timeout=1)
                    break
                except OSError:
                    time.sleep(1)
            else:
                raise RuntimeError("Demo did not start within 60 seconds")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"],
                                            executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto("http://127.0.0.1:7861", wait_until="domcontentloaded")
                page.get_by_role("button", name="Use fictional sample / جرب المثال").click()
                expect(page.get_by_text("Example ready", exact=True)).to_be_visible(timeout=20000)
                page.screenshot(path=str(out / "demo-upload.png"), full_page=True)
                page.get_by_role("tab", name="2 · Ask Tutor").click()
                page.get_by_role("textbox", name="Question / السؤال", exact=True).fill("What does a primary key identify?")
                page.get_by_role("button", name="Ask tutor / اسأل", exact=True).click()
                expect(page.get_by_text("Retrieval-only mode selected.", exact=False)).to_be_visible(timeout=20000)
                page.get_by_text("View source evidence / عرض المصدر", exact=True).click()
                expect(page.get_by_text("PDF page 3", exact=True)).to_be_visible()
                page.screenshot(path=str(out / "demo-evidence.png"), full_page=True)
                page.set_viewport_size({"width": 430, "height": 900})
                page.screenshot(path=str(out / "demo-mobile.png"), full_page=True)
                browser.close()
                if errors:
                    raise AssertionError("Browser JavaScript errors: " + "; ".join(errors))
                print("Browser smoke passed: sample loaded, offline retrieval, source page shown; screenshots captured.")
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait()


if __name__ == "__main__":
    main()
