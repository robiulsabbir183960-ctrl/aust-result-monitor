import os
import requests
from playwright.sync_api import sync_playwright

USER_ID = os.environ.get("USER_ID", "")
PASSWORD = os.environ.get("PASSWORD", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

CHAT_ID = "8573701528"
SEMESTER_LABEL = "Spring, 2025"
FILE_PATH = "last_result.txt"


def load_last_result():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_last_result(result):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(result)


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message},
            timeout=15,
        )
    except Exception as e:
        print("Telegram error:", e)


def extract_result(full_text):
    start_marker = "Result of Semester Final Examinations"
    end_marker = "REMARKS"

    start = full_text.find(start_marker)
    if start == -1:
        return full_text.strip()

    end = full_text.find(end_marker, start)
    if end == -1:
        return full_text[start:].strip()

    return full_text[start:end].strip()


print("BOT STARTED")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page()

    print("Opening login page...")
    page.goto("https://iums.aust.edu/ums-web/login/")
    page.wait_for_selector("#userName")
    page.wait_for_selector("#password")

    page.fill("#userName", USER_ID)
    page.fill("#password", PASSWORD)
    page.keyboard.press("Enter")
    page.wait_for_timeout(5000)

    print("Opening result page...")
    page.get_by_text("Result").click()
    page.wait_for_timeout(2000)

    page.locator("select").first.select_option(label=SEMESTER_LABEL)
    page.get_by_text("Show Result").click()
    page.wait_for_timeout(10000)

    full_text = page.locator("body").inner_text()
    new_result = extract_result(full_text)

    print("Result fetched.")

    old_result = load_last_result()

    if old_result == "":
        save_last_result(new_result)
        print("Initialized result memory. No alert sent.")
    elif new_result != old_result:
        print("CHANGE DETECTED!")
        save_last_result(new_result)
        send_telegram("🔔 AUST Result Update\n\nYour semester result page has changed.")
    else:
        print("No change detected.")

    browser.close()
