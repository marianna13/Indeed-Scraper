from bs4 import BeautifulSoup
import pandas as pd
import requests
import os
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--job_title",
    type=str,
    help="Job title you want to scarpe data for",
)
parser.add_argument(
    "--output_dir",
    type=str,
    default='data',
    help="Directory to save data to, default=data",
)
parser.add_argument(
    "--num_pages",
    type=int,
    default=100,
    help="number of search result pages to scrape",
)


headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'referer': 'https://play.google.com/store/apps',
    'accept-language': 'en-US,en;q=0.9,',
    'cookie': 'prov=6bb44cc9-dfe4-1b95-a65d-5250b3b4c9fb; _ga=GA1.2.1363624981.1550767314; __qca=P0-1074700243-1550767314392; notice-ctt=4%3B1550784035760; _gid=GA1.2.1415061800.1552935051; acct=t=4CnQ70qSwPMzOe6jigQlAR28TSW%2fMxzx&s=32zlYt1%2b3TBwWVaCHxH%2bl5aDhLjmq4Xr',
}


def get_job_urls(URL: str) -> list:
    '''
    Extracts job urls from the search result page given by URL
    '''
    res = requests.get(URL, headers=headers).content
    soup = BeautifulSoup(res, "html.parser")
    job_urls = [a['href'] for a in soup.find_all(
        'a', {"id": lambda x: x and x.startswith('job_')})]
    return job_urls


def get_job_info(job_url: str) -> tuple:
    '''
    Extracts job info from the job URL
    '''
    job_url = 'https://www.indeed.com'+job_url
    res = requests.get(job_url, headers=headers).content
    soup = BeautifulSoup(res, "html.parser")
    title = soup.find('h1').text
    job_info_main = soup.find(
        'div', {"class": lambda x: x and x.startswith('jobsearch')})
    job_info = job_info_main.find(
        'div', {"class": lambda x: x and x.startswith(
            'jobsearch-CompanyInfoWithoutHeaderImage')}
    )
    company = job_info.find(
        'div', {'class': lambda x: x and x.startswith('icl-u')}).text
    job = job_info.find_all(
        'div', {'class': None})
    location = [i.text for i in job][-1]
    try:
        salary_emp, salary_est = [li.text for li in job_info_main.find(
            'ul', {'class': lambda x: x and x.startswith('css-1lyr5hv')}).find_all('li')]
    except AttributeError:
        salary_emp, salary_est = '', ''

    job_description = job_info_main.find('div', {'id': 'jobDescriptionText'})
    description = [d.text.lstrip()
                   for d in job_description.find_all(['p', 'div'])]
    description = ' '.join(description)
    return (title, company, location, salary_emp,
            salary_est, description)


if __name__ == '__main__':
    args = parser.parse_args()
    job_title = args.job_title
    job_title = job_title.replace(' ', '%20')
    output_dir = args.output_dir
    num_pages = args.num_pages

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data = {
        'title': [],
        'company': [],
        'location': [],
        'salary_emp': [],
        'salary_est': [],
        'description': []
    }

    for i in range(0, num_pages*10, 10):
        URL = f'https://www.indeed.com/jobs?q={job_title}&start={i}'
        job_urls = get_job_urls(URL)
        for job_url in tqdm(job_urls, total=len(job_urls)):
            title, company, location, salary_emp, salary_est, description = get_job_info(
                job_url)
            data['title'].append(title)
            data['company'].append(company)
            data['description'].append(description)
            data['location'].append(location)
            data['salary_emp'].append(salary_emp)
            data['salary_est'].append(salary_est)

        pd.DataFrame(data).to_excel(f'data/data{i}.xlsx')
        data = {
            'title': [],
            'company': [],
            'location': [],
            'salary_emp': [],
            'salary_est': [],
            'description': []
        }
