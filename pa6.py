#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 09:27:53 2024

@author: andyguerrero
"""

import time
import re
from time import sleep
import pandas as pd
import requests 
import bs4
from io import StringIO
from os.path import exists
from urllib.parse import urljoin

baseurl = "http://collegecatalog.uchicago.edu/thecollege/programsofstudy/"

# Define patterns
course_pattern = re.compile(r'([A-Z]{4}\s\d{5})\.')
instructors_pattern = re.compile(r'Instructor\(s\): (.*?)(?:Terms Offered:|Prerequisite\(s\):|Equivalent Course\(s\):)', re.DOTALL)
terms_offered_pattern = re.compile(r'Terms Offered: (.*?)(?:Prerequisite\(s\):|Equivalent Course\(s\):|Instructor\(s\):)', re.DOTALL)
prerequisites_pattern = re.compile(r'Prerequisite\(s\): (.*?)(?:Terms Offered:|Equivalent Course\(s\):|Instructor\(s\):)', re.DOTALL)
equivalent_courses_pattern = re.compile(r'Equivalent Course\(s\): (.*?)(?:Terms Offered:|Prerequisite\(s\):|Instructor\(s\):)', re.DOTALL)

def extract_course_info(course):
    # Scrape course info
    title_text = course.find('p', class_='courseblocktitle').get_text()
    course_match = course_pattern.search(title_text)
    if course_match:
        course_number = course_match.group(1)

    # Scrape course description
    course_desc = course.find('p', class_='courseblockdesc').get_text().strip()

    # Scrape detail info
    detail = course.find('p', class_='courseblockdetail')
    if detail:
        detail_text = detail.get_text().replace('\xa0', ' ')

        # Match w/ regex patterns defined earlier
        instructors_match = instructors_pattern.search(detail_text)
        terms_offered_match = terms_offered_pattern.search(detail_text)
        prerequisites_match = prerequisites_pattern.search(detail_text)
        equivalent_courses_match = equivalent_courses_pattern.search(detail_text)

        # Scraped info or None in place
        instructors = instructors_match.group(1).strip() if instructors_match else None
        terms_offered = terms_offered_match.group(1).strip() if terms_offered_match else None
        prerequisites = prerequisites_match.group(1).strip() if prerequisites_match else None
        equivalent_courses = equivalent_courses_match.group(1).strip() if equivalent_courses_match else None

        return {
            'Course Number': course_number,
            'Description': course_desc,
            'Instructor': instructors,
            'Terms Offered': terms_offered,
            'Prerequisites': prerequisites,
            'Equivalent Courses': equivalent_courses
        }
    else:
        return None

def get_program_links(page):
    soup = bs4.BeautifulSoup(page.text, features="html.parser")
    program_links = soup.find('ul', class_='nav leveltwo').find_all('a', href=True)
    program_urls = [urljoin(baseurl, link['href']) for link in program_links]
    return program_urls

def get_data_from_all_programs():
    start_page = requests.get(baseurl)
    program_urls = get_program_links(start_page)
    all_course_data = []
    for url in program_urls:
        response = requests.get(url)
        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            course_blocks = soup.find_all('div', class_='courseblock main')
            for block in course_blocks:
                course_info = extract_course_info(block)
                if course_info:
                    all_course_data.append(course_info)
            time.sleep(3)

    return all_course_data

if __name__ == "__main__":
    courses = get_data_from_all_programs()
    df = pd.DataFrame(courses)
    df.to_csv('coursecatalog.csv', index=False)
    print("Done!")

print(df)

#Find most popular dept
df['Department'] = df['Course Number'].str.extract(r'^([A-Z]{4})')
department_counts = df['Department'].value_counts()

#Find quarter counts
quarter_counts = df['Terms Offered'].value_counts()


