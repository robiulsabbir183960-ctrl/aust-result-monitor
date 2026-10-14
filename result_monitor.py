import os
import requests
from playwright.sync_api import sync_playwright

USER_ID = os.environ.get("USER_ID", "")
PASSWORD = os.environ.get("PASSWORD", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

CHAT_ID = "8573701528"

SEMESTER_LABEL = "Spring, 2025"

FILE_PATH = "last_result.txt"


def load_previous_courses():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())

    return set()


def save_courses(course_codes):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for code in sorted(course_codes):
            f.write(code + "\n")


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=15
        )
    except Exception as e:
        print("Telegram error:", e)


def extract_courses(page):

    results = []

    rows = page.locator("table tr")

    for i in range(rows.count()):

        cells = rows.nth(i).locator("td")

        if cells.count() >= 5:

            course_number = cells.nth(0).inner_text().strip()
            course_title = cells.nth(1).inner_text().strip()
            grade = cells.nth(3).inner_text().strip()
            grade_point = cells.nth(4).inner_text().strip()


            # Ignore empty rows
            if course_number and grade:

                results.append(
                    {
                        "number": course_number,
                        "title": course_title,
                        "grade": grade,
                        "point": grade_point
                    }
                )


    return results



print("BOT STARTED")


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )


    page = browser.new_page()


    print("Opening login page...")

    page.goto(
        "https://iums.aust.edu/ums-web/login/"
    )


    page.wait_for_selector("#userName")
    page.wait_for_selector("#password")


    page.fill(
        "#userName",
        USER_ID
    )

    page.fill(
        "#password",
        PASSWORD
    )


    page.keyboard.press("Enter")

    page.wait_for_timeout(5000)


    print("Opening result page...")


    page.get_by_text("Result").click()

    page.wait_for_timeout(2000)


    page.locator("select").first.select_option(
        label=SEMESTER_LABEL
    )


    page.get_by_text("Show Result").click()

    page.wait_for_timeout(10000)


    print("Extracting result...")


    current_results = extract_courses(page)



    if not current_results:

        print("No result available yet.")


    else:

        previous_courses = load_previous_courses()


        current_codes = {
            r["number"]
            for r in current_results
        }


        new_results = [
            r for r in current_results
            if r["number"] not in previous_courses
        ]


        if new_results:

            message = (
                "🔔 AUST Fall 2025 Result Update\n\n"
                "New Result:\n\n"
            )


            for r in new_results:

                message += (
                    f"{r['number']}\n"
                    f"{r['title']}\n\n"
                    f"Grade: {r['grade']}\n"
                    f"Grade Point: {r['point']}\n\n"
                )


            send_telegram(message)

            print("New result sent.")


        else:

            print("No new result.")


        save_courses(current_codes)



    browser.close()
