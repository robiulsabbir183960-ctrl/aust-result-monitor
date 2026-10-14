import os
import requests
from playwright.sync_api import sync_playwright

USER_ID = os.environ.get("USER_ID", "")
PASSWORD = os.environ.get("PASSWORD", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

CHAT_ID = "8573701528"

SEMESTER_LABEL = "Fall, 2025"

FILE_PATH = "last_result.txt"


def load_previous_courses():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()


def save_courses(courses):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for course in sorted(courses):
            f.write(course + "\n")


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=15,
        )
    except Exception as e:
        print("Telegram error:", e)


def extract_courses(page):

    courses = []

    rows = page.locator("table tbody tr")

    count = rows.count()

    for i in range(count):

        cells = rows.nth(i).locator("td")

        if cells.count() >= 5:

            course_number = cells.nth(0).inner_text().strip()

            course_title = cells.nth(1).inner_text().strip()

            grade = cells.nth(3).inner_text().strip()

            grade_point = cells.nth(4).inner_text().strip()


            if course_number and grade:

                course_data = {
                    "number": course_number,
                    "title": course_title,
                    "grade": grade,
                    "point": grade_point
                }

                courses.append(course_data)

    return courses



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


    current_courses = extract_courses(page)



    previous_courses = load_previous_courses()



    if not current_courses:

        print("No result available yet.")



    else:


        current_codes = {
            c["number"]
            for c in current_courses
        }


        new_courses = [
            c for c in current_courses
            if c["number"] not in previous_courses
        ]



        if not previous_courses:

            save_courses(current_codes)

            print(
                "Baseline created. No Telegram sent."
            )


        elif new_courses:


            message = (
                "🔔 AUST Fall 2025 Result Update\n\n"
                "New Result:\n\n"
            )


            for c in new_courses:

                message += (
                    f"{c['number']}\n"
                    f"{c['title']}\n\n"
                    f"Grade: {c['grade']}\n"
                    f"Grade Point: {c['point']}\n\n"
                )


            send_telegram(message)


            save_courses(current_codes)


            print(
                "New result sent."
            )


        else:

            print(
                "No new result."
            )



    browser.close()
