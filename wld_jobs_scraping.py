import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


def fetch_job_listings(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    departments = soup.find_all("div", class_="border-b border-e5e5e5")
    job_list = []

    for department in departments:
        department_text = department.get_text(" | ", strip=True)
        job_details = department_text.split("Apply now")
        for job in job_details:
            if job.strip():
                unwanted_suffix = " | / | Remote | "
                job = job[: -len(unwanted_suffix)]
                job_list.append(job.strip())

    return job_list


def check_for_new_jobs(url, storage_file="jobs.json"):
    try:
        with open(storage_file, "r") as file:
            old_jobs = json.load(file)
    except FileNotFoundError:
        old_jobs = []

    current_jobs = fetch_job_listings(url)

    new_jobs = [job for job in current_jobs if job not in old_jobs]
    removed_jobs = [job for job in old_jobs if job not in current_jobs]

    with open(storage_file, "w") as file:
        json.dump(current_jobs, file)

    return new_jobs, removed_jobs


def send(token_tg, id_tg, text):
    url = (
        "https://api.telegram.org/bot"
        + token_tg
        + "/sendMessage?chat_id="
        + id_tg
        + "&text="
        + text
        + ""
    )
    resp = requests.get(url)
    r = resp.json()
    return


def notify_new(token_tg, id_tg, new_jobs):
    for job in new_jobs:
        text = f"New Job Listing Found: {job}"
        send(token_tg, id_tg, text)


def notify_removed(token_tg, id_tg, removed_jobs):
    for job in removed_jobs:
        text = f"Jobs removed: {job}"
        send(token_tg, id_tg, text)


def main(url, interval):
    token_tg = os.getenv("token")
    id_tg = os.getenv("id_tg")

    while True:
        print(
            f"Checking for new jobs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        new_jobs, removed_jobs = check_for_new_jobs(url)
        if new_jobs:
            notify_new(token_tg, id_tg, new_jobs)

        if removed_jobs:
            notify_removed(token_tg, id_tg, removed_jobs)

        time.sleep(interval)


if __name__ == "__main__":
    job_url = "https://worldcoin.org/careers"
    main(job_url, interval=20)
