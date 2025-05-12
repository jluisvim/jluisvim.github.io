#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: 
#       José-Luis Vilchis
# Description:
#       Script for transform html to csv courses.
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

import csv
from bs4 import BeautifulSoup

def extract_courses_from_html(html_content):
    """Extract course data from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    courses_data = []
    
    # Find all tabcontent divs
    for tab in soup.find_all('div', class_='tabcontent'):
        year = tab['id']
        institution = tab.find('i').text.replace('Courses taught at ', '').replace('Course taught at ', '').replace(')', '').strip()
        
        # Extract courses from tables
        for row in tab.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) == 3:  # Ensure it's a data row
                course_type = cols[0].get_text(strip=True)
                course_name = cols[1].get_text(strip=True)
                duration = cols[2].get_text(strip=True)
                
                courses_data.append({
                    'Academic Year': year,
                    'Institution': institution,
                    'Course Type': course_type,
                    'Course Name': course_name,
                    'Duration': duration
                })
    
    return courses_data

def write_to_csv(courses_data, output_file):
    """Write course data to CSV file"""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Academic Year', 'Institution', 'Course Type', 'Course Name', 'Duration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for course in courses_data:
            writer.writerow(course)

def main():
    # Read HTML file
    with open('../teaching.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Extract data
    courses = extract_courses_from_html(html_content)
    
    # Write to CSV
    write_to_csv(courses, 'courses.csv')
    print(f"Successfully extracted {len(courses)} courses to courses.csv")

if __name__ == '__main__':
    main()
