# Script Python (bibtexparser)
#!/usr/bin/env python3
import bibtexparser
from bibtexparser.bparser import BibTexParser
from datetime import datetime
import shutil
import os
import csv
from collections import defaultdict
import re

# Configuration
CONFIG = {
    'COURSES_CSV': "data/courses.csv",
    'PRESENTATIONS_CSV': "data/presentations.csv",
    'NEWS_CSV': "data/news.csv",
    'BIB_FILE': "data/mybiblio.bib",
    'TEMPLATE_FILE': "template_base.html",
    'OUTPUT_DIR': "dist",
    'CSS_FILE': "styles.css",
    'IMG_DIR': "../../imgs",
    'AUTHOR_VARIANTS': [
        "José-Luis Vilchis-Medina",
        "José-Luis Vilchis Medina",
        "Vilchis-Medina, José-Luis",
        "J.L. Vilchis-Medina",
        "Vilchis-Medina, J.L.",
        ] ,
    'DOMAIN_MAP': {
        "log": "Logic",
        "nmr": "NMR",
        "rob": "Robotics",
        "ctl": "Control",
        "dbs": "Databases",
        "sim": "Similarity",
        "info": "Information",
        "res": "Resilience",
    }
}

def sanitize_html(text):
    """Escape special HTML characters"""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


class PublicationGenerator:
    def __init__(self, config):
        self.config = config
        
    def load_bibtex(self):
        """Load and parse BibTeX file"""
        parser = BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = True
        with open(self.config['BIB_FILE'], encoding="utf-8") as f:
            return bibtexparser.load(f, parser=parser)
    
    def generate_stats(self, bib_db):
        """Generate publication statistics"""
        stats = {
            'total_publications': len(bib_db.entries),
            'years': {},
            'domains': {}
        }
        
        for entry in bib_db.entries:
            year = entry.get("year", "Unknown")
            stats['years'][year] = stats['years'].get(year, 0) + 1
            
            domain = "other"
            if "keywords" in entry:
                domain = entry["keywords"].split(",")[0].strip().lower()
            domain_display = self.config['DOMAIN_MAP'].get(domain, domain.title())
            stats['domains'][domain_display] = stats['domains'].get(domain_display, 0) + 1
        
        return stats
    
    def get_publication_type(self, entry):
        """Determine publication type with improved logic"""
        # Check for preprints first (arXiv, bioRxiv, or note field)
        if (
            entry.get("archiveprefix", "").lower() in ["arxiv", "biorxiv"] or
            entry.get("eprinttype", "").lower() in ["arxiv", "biorxiv"] or
            ("note" in entry and "preprint" in entry["note"].lower()) or
            ("journal" in entry and "arxiv" in entry["journal"].lower())
        ):
            return "preprint"
        
        # Rest of the logic for journals and conferences
        if "journal" in entry:
            return "journal"
        elif "booktitle" in entry:
            keywords = entry.get("keywords", "").lower()
            if "international" in keywords:
                return "conference-int"
            elif "national" in keywords:
                return "conference-nat"
            elif any(word in keywords for word in ["sig", "acm", "ieee", "world"]):
                return "conference-int"
            else:
                return "conference-nat"
        return "other"
    
    def build_venue_string(self, entry):
        """Build formatted venue string"""
        venue = entry.get("journal", entry.get("booktitle", ""))
        if "volume" in entry:
            venue += f", {entry['volume']}"
            if "number" in entry:
                venue += f"({entry['number']})"
        if "pages" in entry:
            venue += f", pp. {entry['pages']}"
        return sanitize_html(venue)
    
    def build_links(self, entry):
        """Generate publication links"""
        links = []
        if "url" in entry:
            links.append(f'<a href="{entry["url"]}" target="_blank" class="publication-link">PDF</a>')
        if "doi" in entry:
            links.append(f'<a href="https://doi.org/{entry["doi"]}" target="_blank" class="publication-link">DOI</a>')
        if "arxiv" in entry:
            links.append(f'<a href="https://arxiv.org/abs/{entry["arxiv"]}" target="_blank" class="publication-link">arXiv</a>')
        return links
    
    def normalize_name(self, name):
        """Normalize author name for comparison"""
        if not name:
            return ""
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', '', name.strip().lower())
        # Sort name parts to handle different order formats
        parts = sorted(name.split())
        return ' '.join(parts)
    
    def process_authors(self, authors_str):
        """Process author string and highlight matching authors"""
        if not authors_str:
            return ""
        
        author_list = authors_str.split(" and ")
        highlighted_authors = []
        
        for author in author_list:
            normalized_author = self.normalize_name(author)
            is_highlighted = False
            
            # Compare with all author variants from config
            for variant in self.config.get('AUTHOR_VARIANTS', []):
                if self.normalize_name(variant) == normalized_author:
                    is_highlighted = True
                    break
            
            if is_highlighted:
                highlighted_authors.append(f'<u><strong>{sanitize_html(author)}</strong></u>')
            else:
                highlighted_authors.append(sanitize_html(author))
        
        return ", ".join(highlighted_authors)
    
    def generate_publications_html(self, bib_db, color_coded=True):
        """Generate HTML for publications with optional color coding"""
        entries_by_year = defaultdict(list)
        for entry in bib_db.entries:
            year = entry.get("year", "Unknown")
            entries_by_year[year].append(entry)

        years = sorted(entries_by_year.keys(), reverse=True)
        
        html = ['<div class="publications-container">']
        
        if color_coded:
            html.append('''
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color journal-color"></div>
                    <span>Journal</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color conference-int-color"></div>
                    <span>International Conference</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color conference-nat-color"></div>
                    <span>National Conference</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color preprint-color"></div>
                    <span>Preprint/Other</span>
                </div>
            </div>
            ''')
        
        html.append('<div class="publication-tabs">')
        for i, year in enumerate(years):
            active_class = " active" if i == 0 else ""
            html.append(f'<button class="publication-tab{active_class}" onclick="openPublicationTab(event, \'pub-{year}\')">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            html.append(f'<div id="pub-{year}" class="publication-content" style="display:{display_style}">')
            
            for entry in entries_by_year[year]:
                pub_type = self.get_publication_type(entry) if color_coded else None
                title = sanitize_html(entry.get("title", "Untitled"))
                authors = self.process_authors(entry.get("author", ""))
                venue = self.build_venue_string(entry)
                links = self.build_links(entry)
                
                color_indicator = f'<span class="color-indicator {pub_type}"></span>' if color_coded and pub_type else ''
                
                html.append(f'''
                <div class="publication">
                    <h3 class="publication-title">{color_indicator}{title}</h3>
                    <div class="publication-authors">{authors}</div>
                    <div class="publication-venue">{venue}</div>
                    <div class="publication-links">{' '.join(links)}</div>
                </div>
                ''')
            
            html.append('</div>')

        html.append('</div>')
        return "\n".join(html)
    
    def generate_stats_html(self, stats):
        """Generate statistics panel HTML"""
        top_domains = sorted(stats['domains'].items(), key=lambda x: x[1], reverse=True)[:3]
        
        return f"""
        <aside class="stats-panel">
            <h3>Research Metrics</h3>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-value">{stats['total_publications']}</div>
                    <div class="stat-label">Total Publications</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(stats['years'])}</div>
                    <div class="stat-label">Years Active</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{top_domains[0][1]}</div>
                    <div class="stat-label">{top_domains[0][0]} Publications</div>
                </div>
            </div>
        </aside>
        """
    
    def add_tab_script(self):
        """Add JavaScript for tab functionality"""
        return """
        <script>
        function openPublicationTab(evt, tabName) {
            const tabContents = document.getElementsByClassName("publication-content");
            for (let i = 0; i < tabContents.length; i++) {
                tabContents[i].style.display = "none";
            }
            
            const tabButtons = document.getElementsByClassName("publication-tab");
            for (let i = 0; i < tabButtons.length; i++) {
                tabButtons[i].classList.remove("active");
            }
            
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.classList.add("active");
        }
        </script>
        """


class TeachingGenerator:
    def __init__(self, config):
        self.config = config
    
    def load_courses(self):
        """Load courses data from CSV"""
        courses_by_year = {}
        
        with open(self.config['COURSES_CSV'], mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                year = row['Academic Year']
                if year not in courses_by_year:
                    courses_by_year[year] = {
                        'institution': row['Institution'],
                        'courses': []
                    }
                courses_by_year[year]['courses'].append({
                    'type': row['Lecture Type'],
                    'name': row['Lecture Name'],
                    'duration': row['Duration']
                })
        
        return courses_by_year
    
    def generate_courses_html(self, courses_data):
        """Generate HTML for courses with year tabs"""
        years = sorted(courses_data.keys(), reverse=True)
        
        html = ['<div class="courses-container">']
        html.append('<div class="course-tabs">')
        
        for i, year in enumerate(years):
            active_class = " active" if i == 0 else ""
            html.append(f'<button class="course-tab{active_class}" onclick="openCourseTab(event, \'courses-{year}\')">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            institution = courses_data[year]['institution']
            
            html.append(f'<div id="courses-{year}" class="course-content" style="display:{display_style}">')
            html.append(f'<p class="institution"><i>Lectures taught at {institution}</i></p>')
            html.append('<hr class="course-separator">')
            html.append('<table class="course-table">')
            
            for course in courses_data[year]['courses']:
                html.append(f"""
                <tr>
                    <td class="course-type">{course['type']}</td>
                    <td class="course-name">{course['name']}</td>
                    <td class="course-duration">{course['duration']}</td>
                </tr>
                """)
            
            html.append('</table>')
            html.append('</div>')
        
        html.append('</div>')
        return "\n".join(html)
    
    def generate_tab_script(self):
        """Generate JavaScript for tab functionality"""
        return """
        <script>
        function openCourseTab(evt, tabId) {
            const contents = document.getElementsByClassName("course-content");
            for (let i = 0; i < contents.length; i++) {
                contents[i].style.display = "none";
            }
            
            const tabs = document.getElementsByClassName("course-tab");
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove("active");
            }
            
            document.getElementById(tabId).style.display = "block";
            evt.currentTarget.classList.add("active");
        }
        </script>
        """

class NewsGenerator:
    def __init__(self, config):
        self.config = config
    
    def load_news(self):
        """Carga CSV con eventos y links separados"""
        try:
            with open(self.config['NEWS_CSV'], mode='r', encoding='utf-8') as csvfile:
                return sorted([
                    {
                        'date': datetime.strptime(row['date'], '%Y-%m-%d'),
                        'event': row['event'].strip(),
                        'link': row.get('link', '').strip()
                    } for row in csv.DictReader(csvfile)
                ], key=lambda x: x['date'], reverse=False)[:3]
        except FileNotFoundError:
            return []

    def generate_news_html(self, news_items):
        """Genera lista con links solo en el nombre del evento"""
        if not news_items:
            return ""
        
        items = []
        for item in news_items:
            event = sanitize_html(item['event'])
            if item['link']:
                event = f'<a href="{item["link"]}" target="_blank">{event}</a>'
            
            date_str = item['date'].strftime("%Y-%m-%d")
            if item['date'].date() < datetime.now().date():
                date_str = f'<del>{date_str}</del>'
            
            items.append(f'<li><b>{date_str}</b>: {event}</li>')
        
        return f'''
<div class="updates">
    <h2>News - Updates</h2>
        <ul>
            {"".join(items)}
        </ul>
</div>
'''


class PresentationGenerator:
    def __init__(self, config):
        self.config = config
    
    def load_presentations(self):
        """Load presentations data from CSV"""
        presentations_by_year = defaultdict(list)
        
        with open(self.config['PRESENTATIONS_CSV'], mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                year = row['Año']
                presentations_by_year[year].append({
                    'title': row['Título'],
                    'event': row['Evento'],
                    'location': row['Lugar'],
                    'month': row['Mes'],
                    'authors': row['Autores']
                })
        
        return dict(presentations_by_year)
    
    def generate_presentations_html(self, presentations_data):
        """Generate HTML for presentations with year tabs"""
        years = sorted(presentations_data.keys(), reverse=True)
        
        html = ['<div class="presentations-container">']
        html.append('<div class="presentation-tabs">')
        
        for i, year in enumerate(years):
            active_class = " active" if i == 0 else ""
            html.append(f'<button class="presentation-tab{active_class}" onclick="openPresentationTab(event, \'presentations-{year}\')">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            
            html.append(f'<div id="presentations-{year}" class="presentation-content" style="display:{display_style}">')
            

#                     <div class="presentation-authors">{presentation['authors']}</div>
            for presentation in presentations_data[year]:
                title = f"<b><em>{presentation['title']}</em></b>"
                html.append(f"""
                <div class="presentation-item">
                    <h3 class="presentation-title">{title}</h3>
                    <div class="presentation-meta">
                        <span class="presentation-event">{presentation['event']}</span> | 
                        <span class="presentation-location">{presentation['location']}</span> | 
                        <span class="presentation-date">{presentation['month']} {year}</span>
                    </div>
                </div>
                """)
            
            html.append('</div>')
        
        html.append('</div>')
        return "\n".join(html)
    
    def generate_tab_script(self):
        """Generate JavaScript for tab functionality"""
        return """
        <script>
        function openPresentationTab(evt, tabId) {
            const contents = document.getElementsByClassName("presentation-content");
            for (let i = 0; i < contents.length; i++) {
                contents[i].style.display = "none";
            }
            
            const tabs = document.getElementsByClassName("presentation-tab");
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove("active");
            }
            
            document.getElementById(tabId).style.display = "block";
            evt.currentTarget.classList.add("active");
        }
        </script>
        """

class SiteBuilder:
    def __init__(self, config):
        self.config = config
        self.pub_gen = PublicationGenerator(config)
        self.teach_gen = TeachingGenerator(config)
        self.news_gen = NewsGenerator(config)
        self.pres_gen = PresentationGenerator(config)
    
    def build_site(self):
        """Main build function"""
        start_time = datetime.now()
        
        # Create output directory
        os.makedirs(self.config['OUTPUT_DIR'], exist_ok=True)
        
        # Load data
        bib_db = self.pub_gen.load_bibtex()
        stats = self.pub_gen.generate_stats(bib_db)
        courses_data = self.teach_gen.load_courses()
        news_items = self.news_gen.load_news()
        presentations = self.pres_gen.load_presentations()
#         pres_stats = self.pres_gen.generate_stats(presentations)
        
        # Read template
        with open(self.config['TEMPLATE_FILE'], "r", encoding="utf-8") as f:
            template = f.read()

        # Generate and insert content
        template = template.replace("<!-- STATS_PANEL -->", self.pub_gen.generate_stats_html(stats))
        template = template.replace("<!-- PUBLICATIONS -->", 
                                  self.pub_gen.generate_publications_html(bib_db, color_coded=True))
        template = template.replace("<!-- PUB_SCRIPTS -->", self.pub_gen.add_tab_script())
        template = template.replace("<!-- COURSES_SECTION -->", self.teach_gen.generate_courses_html(courses_data))
        template = template.replace("<!-- COURSES_SCRIPT -->", self.teach_gen.generate_tab_script())
        template = template.replace("<!-- NEWS_SECTION -->", self.news_gen.generate_news_html(news_items))  # Add this line
        
        template = template.replace("<!-- PRESENTATIONS_SECTION -->", self.pres_gen.generate_presentations_html(presentations))
#         template = template.replace("<!-- PRES_STATS -->", self.pres_gen.generate_stats_html(pres_stats))
        template = template.replace("<!-- PRES_SCRIPTS -->", self.pres_gen.generate_tab_script())

        # Write output file
        output_path = os.path.join(self.config['OUTPUT_DIR'], "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)
        
        # Copy static assets
        self.copy_assets()
        
        # Calculate build time
        build_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Site built successfully in {build_time:.2f} seconds")
        print(f"📁 Output directory: {os.path.abspath(self.config['OUTPUT_DIR'])}")
    
    def copy_assets(self):
        """Copy all required static assets"""
        # Copy CSS
        shutil.copy2(self.config['CSS_FILE'], self.config['OUTPUT_DIR'])
        
        # Copy profile image if exists
        profile_img_src = os.path.join(self.config['IMG_DIR'], "photo_opt3.jpeg")
        if os.path.exists(profile_img_src):
            os.makedirs(os.path.join(self.config['OUTPUT_DIR'], "imgs"), exist_ok=True)
            shutil.copy2(profile_img_src, os.path.join(self.config['OUTPUT_DIR'], "imgs"))

if __name__ == "__main__":
    builder = SiteBuilder(CONFIG)
    builder.build_site()
