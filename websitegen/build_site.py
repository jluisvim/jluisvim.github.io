#!/usr/bin/env python3
import bibtexparser
from bibtexparser.bparser import BibTexParser
from datetime import datetime
import shutil
import os
import csv
from collections import defaultdict
import re
import unicodedata

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
    ],
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
        try:
            parser = BibTexParser(common_strings=True)
            parser.ignore_nonstandard_types = True
            with open(self.config['BIB_FILE'], encoding="utf-8") as f:
                return bibtexparser.load(f, parser=parser)
        except FileNotFoundError:
            print(f"⚠️ BibTeX file not found: {self.config['BIB_FILE']}")
            return bibtexparser.loads('')
    
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
        """Determine publication type"""
        # Check for preprints
        if (
            entry.get("archiveprefix", "").lower() in ["arxiv", "biorxiv"] or
            entry.get("eprinttype", "").lower() in ["arxiv", "biorxiv"] or
            ("note" in entry and "preprint" in entry["note"].lower()) or
            ("journal" in entry and "arxiv" in entry["journal"].lower())
        ):
            return "preprint"
        
        # Journals and conferences
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
        """Build formatted venue string with proper Unicode accents"""
        journal = entry.get("journal", "")
        booktitle = entry.get("booktitle", "")
        
        # Use booktitle for conferences, journal for articles
        raw_venue = journal if journal else booktitle
        
        # Convert LaTeX accents to Unicode
        venue = self.latex_to_unicode(raw_venue)
        
        # Append volume, number, pages if available
        if "volume" in entry:
            venue += f", {entry['volume']}"
            if "number" in entry:
                venue += f"({entry['number']})"
        if "pages" in entry:
            venue += f", pp. {entry['pages']}"
        
        return sanitize_html(venue)
    
    def build_link_icons(self, entry):
        """Generate publication link icons with colorblind-friendly design"""
        links = []
        
        # PDF icon
        if "url" in entry:
            links.append(f'''
            <a href="{entry["url"]}" target="_blank" class="link-icon pdf" 
               title="PDF" aria-label="PDF" rel="noopener">
                <svg width="12" height="12" viewBox="0 0 24 24">
                    <rect x="4" y="4" width="16" height="16" rx="2" fill="none" 
                          stroke="#c62828" stroke-width="1.5"/>
                    <path d="M8 8h8M8 12h8M8 16h5" stroke="#c62828" stroke-width="1.5" 
                          stroke-linecap="round"/>
                </svg>
            </a>''')
        
        # DOI icon
        if "doi" in entry:
            links.append(f'''
            <a href="https://doi.org/{entry["doi"]}" target="_blank" 
               class="link-icon doi" title="DOI" aria-label="DOI" rel="noopener">
                <svg width="12" height="12" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="3" fill="none" stroke="#1565c0" 
                            stroke-width="1.5"/>
                    <path d="M7 12H5M19 12h-2M12 5v2M12 19v-2" stroke="#1565c0" 
                          stroke-width="1.5" stroke-linecap="round"/>
                    <circle cx="12" cy="12" r="8" fill="none" stroke="#1565c0" 
                            stroke-width="1.5"/>
                </svg>
            </a>''')
        
        # arXiv icon
        arxiv_id = None
        if "arxiv" in entry:
            arxiv_id = entry["arxiv"]
        elif "eprint" in entry and ("archiveprefix" in entry or "eprinttype" in entry):
            archive = entry.get("archiveprefix", entry.get("eprinttype", "")).lower()
            if archive == "arxiv":
                arxiv_id = entry["eprint"]
        
        if arxiv_id:
            links.append(f'''
            <a href="https://arxiv.org/abs/{arxiv_id}" target="_blank" 
               class="link-icon arxiv" title="arXiv" aria-label="arXiv" rel="noopener">
                <svg width="12" height="12" viewBox="0 0 24 24">
                    <path d="M19 4H5C3.9 4 3 4.9 3 6v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z" 
                          fill="none" stroke="#2e7d32" stroke-width="1.5"/>
                    <path d="M7 8h10M7 12h10M7 16h7" stroke="#2e7d32" stroke-width="1.5" 
                          stroke-linecap="round"/>
                </svg>
            </a>''')
        
        return links

    def normalize_author_for_matching(self, name):
        """Normalize for author matching: handle accents, braces, and name order."""
        if not name:
            return ""
        # Remove \textbf{...}
        name = re.sub(r'\\textbf\{([^}]*)\}', r'\1', name)
        # Convert LaTeX accents to Unicode
        name = self.latex_to_unicode(name)
        # Remove diacritics for robust matching
        name = ''.join(c for c in unicodedata.normalize('NFD', name)
                       if unicodedata.category(c) != 'Mn')
        name = name.strip().lower()
        # Handle "Last, First"
        if ',' in name:
            last, first = [p.strip() for p in name.split(',', 1)]
            name = f"{first} {last}".strip()
        # Normalize whitespace
        return re.sub(r'\s+', ' ', name)
    
    def normalize_name(self, name):
        """Normalize author name for comparison"""
        if not name:
            return ""
        name = re.sub(r'[^\w\s]', '', name.strip().lower())
        parts = sorted(name.split())
        return ' '.join(parts)

    def latex_to_unicode(self, text):
        """Convert common LaTeX accent commands to Unicode characters (including in titles)."""
        if not text:
            return text
    
        # Helper for accents
        def replace_accent(match):
            cmd, char = match.groups()
            if cmd == "'":
                return {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú',
                        'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú'}.get(char, char)
            elif cmd == "`":
                return {'a': 'à', 'e': 'è'}.get(char, char)
            elif cmd == '"':
                return {'a': 'ä', 'e': 'ë', 'i': 'ï', 'o': 'ö', 'u': 'ü'}.get(char, char)
            elif cmd == "~":
                return {'n': 'ñ', 'N': 'Ñ'}.get(char, char)
            elif cmd == "^":  # ← Añadido: circumflex
                return {'a': 'â', 'e': 'ê', 'i': 'î', 'o': 'ô', 'u': 'û',
                        'A': 'Â', 'E': 'Ê', 'I': 'Î', 'O': 'Ô', 'U': 'Û'}.get(char, char)
            return char
    
        # Replace \cmd{char} and \cmd char
        text = re.sub(r"\\([`'\"~^])\{([aeiouAEIOU])\}", replace_accent, text)
        text = re.sub(r"\\([`'\"~^])([aeiouAEIOU])", replace_accent, text)
        # Cedilla
        text = re.sub(r"\\c\{([cC])\}", lambda m: 'ç' if m.group(1) == 'c' else 'Ç', text)
        # Remove protection braces
        text = text.replace('{', '').replace('}', '')
        return text
    
    def process_authors(self, authors_str):
        """Process and highlight authors with proper LaTeX-to-Unicode conversion."""
        if not authors_str:
            return ""
        
        author_list = [a.strip() for a in authors_str.split(" and ") if a.strip()]
        normalized_variants = {
            self.normalize_author_for_matching(var) for var in self.config.get('AUTHOR_VARIANTS', [])
        }
        
        highlighted = []
        for author in author_list:
            # Use full Unicode for display
            display_name = re.sub(r'\\textbf\{([^}]*)\}', r'\1', author)
            display_name = self.latex_to_unicode(display_name)
            
            # Normalize for comparison (accent-insensitive)
            normalized = self.normalize_author_for_matching(author)
            is_me = normalized in normalized_variants
            
            if is_me:
                highlighted.append(f'<u><strong>{sanitize_html(display_name)}</strong></u>')
            else:
                highlighted.append(sanitize_html(display_name))
        
        return ", ".join(highlighted)
    
    def generate_publications_html(self, bib_db, color_coded=True):
        """Generate HTML for publications"""
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
            html.append(f'<button class="publication-tab{active_class}" data-year="{year}">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            html.append(f'<div id="pub-{year}" class="publication-content" style="display:{display_style}">')
            
            for entry in entries_by_year[year]:
                pub_type = self.get_publication_type(entry) if color_coded else None
#                 title = sanitize_html(entry.get("title", "Untitled"))
                raw_title = entry.get("title", "Untitled")
                clean_title = self.latex_to_unicode(raw_title)
                title = sanitize_html(clean_title)

                authors = self.process_authors(entry.get("author", ""))
                venue = self.build_venue_string(entry)
                link_icons = self.build_link_icons(entry)
                
                color_indicator = f'<span class="color-indicator {pub_type}"></span>' if color_coded and pub_type else ''
                
                icons_html = ""
                if link_icons:
                    icons_html = f'<span class="title-icons-container">{"".join(link_icons)}</span>'
                
                html.append(f'''
                <div class="publication">
                    <div class="publication-header">
                        {color_indicator}
                        <h3 class="publication-title">{title}</h3>
                        {icons_html}
                    </div>
                    <div class="publication-meta">
                        <div class="publication-authors">{authors}</div>
                        <div class="publication-venue">{venue}</div>
                    </div>
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
                    <div class="stat-value">{top_domains[0][1] if top_domains else 0}</div>
                    <div class="stat-label">{top_domains[0][0] if top_domains else 'N/A'}</div>
                </div>
            </div>
        </aside>
        """
    
    def add_tab_script(self):
        """Add JavaScript for tab functionality (solo para publicaciones internas)"""
        return """
        <script>
        // Solo para pestañas de publicaciones
        document.addEventListener('DOMContentLoaded', function() {
            const pubTabs = document.querySelectorAll('.publication-tab');
            pubTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const year = this.getAttribute('data-year');
                    
                    // Hide all publication contents
                    document.querySelectorAll('.publication-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    
                    // Remove active class from all publication tabs
                    pubTabs.forEach(t => t.classList.remove('active'));
                    
                    // Show selected content and mark tab as active
                    document.getElementById('pub-' + year).style.display = 'block';
                    this.classList.add('active');
                });
            });
            
            // Para pestañas de cursos
            const courseTabs = document.querySelectorAll('.course-tab');
            courseTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const year = this.getAttribute('data-year');
                    
                    // Hide all course contents
                    document.querySelectorAll('.course-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    
                    // Remove active class from all course tabs
                    courseTabs.forEach(t => t.classList.remove('active'));
                    
                    // Show selected content and mark tab as active
                    document.getElementById('courses-' + year).style.display = 'block';
                    this.classList.add('active');
                });
            });
            
            // Para pestañas de presentaciones
            const presTabs = document.querySelectorAll('.presentation-tab');
            presTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const year = this.getAttribute('data-year');
                    
                    // Hide all presentation contents
                    document.querySelectorAll('.presentation-content').forEach(content => {
                        content.style.display = 'none';
                    });
                    
                    // Remove active class from all presentation tabs
                    presTabs.forEach(t => t.classList.remove('active'));
                    
                    // Show selected content and mark tab as active
                    document.getElementById('presentations-' + year).style.display = 'block';
                    this.classList.add('active');
                });
            });
        });
        </script>
        """


class TeachingGenerator:
    def __init__(self, config):
        self.config = config
    
    def load_courses(self):
        """Load courses data from CSV"""
        courses_by_year = {}
        
        try:
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
        except FileNotFoundError:
            print(f"⚠️ Courses file not found: {self.config['COURSES_CSV']}")
        
        return courses_by_year
    
    def generate_courses_html(self, courses_data):
        """Generate HTML for courses with year tabs"""
        if not courses_data:
            return '<p>No course data available.</p>'
        
        years = sorted(courses_data.keys(), reverse=True)
        
        html = ['<div class="courses-container">']
        html.append('<div class="course-tabs">')
        
        for i, year in enumerate(years):
            active_class = " active" if i == 0 else ""
            html.append(f'<button class="course-tab{active_class}" data-year="{year}">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            institution = courses_data[year]['institution']
            
            html.append(f'<div id="courses-{year}" class="course-content" style="display:{display_style}">')
            html.append(f'<p class="institution"><i>Lectures taught at {institution}</i></p>')
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


class NewsGenerator:
    def __init__(self, config):
        self.config = config
    
    def load_news(self):
        """Load CSV with events and links separated"""
        try:
            with open(self.config['NEWS_CSV'], mode='r', encoding='utf-8') as csvfile:
                news_items = [
                    {
                        'date': datetime.strptime(row['date'], '%Y-%m-%d'),
                        'event': row['event'].strip(),
                        'link': row.get('link', '').strip()
                    } for row in csv.DictReader(csvfile)
                ]
                
                # Filter out news items with dates in the past
                future_news_items = [item for item in news_items if item['date'].date() >= datetime.now().date()]
                
                # Sort the remaining news items by date
                future_news_items.sort(key=lambda x: x['date'], reverse=False)
                
                # Return only the first 3 future news items
                return future_news_items[:3]
        except FileNotFoundError:
            print(f"⚠️ News file not found: {self.config['NEWS_CSV']}")
            return []

    def generate_news_html(self, news_items):
        """Generate news list with links only in event names"""
        if not news_items:
            return ""
        
        items = []
        for item in news_items:
            event = sanitize_html(item['event'])
            if item['link']:
                event = f'<a href="{item["link"]}" target="_blank" rel="noopener">{event}</a>'
            
            date_str = item['date'].strftime("%Y-%m-%d")
            if item['date'].date() < datetime.now().date():
                date_str = f'<del>{date_str}</del>'
            
            items.append(f'<li><b>{date_str}</b>: {event}</li>')
        
        return f'''
<div class="updates">
    <h3>News & Updates</h3>
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
        
        try:
            with open(self.config['PRESENTATIONS_CSV'], mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    year = row['Year']
                    presentations_by_year[year].append({
                        'title': row['Title'],
                        'event': row['Event'],
                        'location': row['Place'],
                        'month': row['Month'],
                        'authors': row.get('Authors', '')
                    })
        except FileNotFoundError:
            print(f"⚠️ Presentations file not found: {self.config['PRESENTATIONS_CSV']}")
        
        return dict(presentations_by_year)
    
    def generate_presentations_html(self, presentations_data):
        """Generate HTML for presentations with year tabs"""
        if not presentations_data:
            return '<p>No presentations available.</p>'
        
        years = sorted(presentations_data.keys(), reverse=True)
        
        html = ['<div class="presentations-container">']
        html.append('<div class="presentation-tabs">')
        
        for i, year in enumerate(years):
            active_class = " active" if i == 0 else ""
            html.append(f'<button class="presentation-tab{active_class}" data-year="{year}">{year}</button>')
        html.append('</div>')
        
        for i, year in enumerate(years):
            display_style = "block" if i == 0 else "none"
            
            html.append(f'<div id="presentations-{year}" class="presentation-content" style="display:{display_style}">')
            
            for presentation in presentations_data[year]:
                title = sanitize_html(presentation['title'])
                if presentation.get('authors'):
                    title = f"<em>{title}</em>"
                
                html.append(f"""
                <div class="presentation-item">
                    <div class="presentation-title">{title}</div>
                    <div class="presentation-meta">
                        <span>{presentation['event']}</span> | 
                        <span>{presentation['location']}</span> | 
                        <span>{presentation['month']} {year}</span>
                    </div>
                </div>
                """)
            
            html.append('</div>')
        
        html.append('</div>')
        return "\n".join(html)


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
        
        # Read template
        with open(self.config['TEMPLATE_FILE'], "r", encoding="utf-8") as f:
            template = f.read()

        # Generate and insert content
        template = template.replace("<!-- STATS_PANEL -->", self.pub_gen.generate_stats_html(stats))
        template = template.replace("<!-- PUBLICATIONS -->", 
                                  self.pub_gen.generate_publications_html(bib_db, color_coded=True))
        template = template.replace("<!-- PUB_SCRIPTS -->", self.pub_gen.add_tab_script())
        template = template.replace("<!-- COURSES_SECTION -->", self.teach_gen.generate_courses_html(courses_data))
        template = template.replace("<!-- NEWS_SECTION -->", self.news_gen.generate_news_html(news_items))
        template = template.replace("<!-- PRESENTATIONS_SECTION -->", self.pres_gen.generate_presentations_html(presentations))

        # Add scroll highlighting script CON OPCIÓN DE CLICK PARA ACTIVAR
        template = template.replace("<!-- MAIN_SCRIPT -->", self._generate_enhanced_scroll_script())

        # Generate update
        current_date = datetime.now().strftime("%B %d, %Y")
        template = template.replace("<!-- LAST_UPDATED -->", current_date)

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
    
    def _generate_enhanced_scroll_script(self):
        """Generate JavaScript for scroll highlighting with click activation"""
        return """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const sections = document.querySelectorAll('.main-content section');
            const navLinks = document.querySelectorAll('.sidebar-nav a');
            
            // Función para activar una sección específica
            function activateSection(sectionId, scrollTo = true) {
                // Remover clase active de todas las secciones
                sections.forEach(section => {
                    section.classList.remove('active');
                });
                
                // Remover clase active de todos los enlaces
                navLinks.forEach(link => {
                    link.classList.remove('active');
                });
                
                // Activar la sección seleccionada
                const targetSection = document.getElementById(sectionId);
                if (targetSection) {
                    targetSection.classList.add('active');
                    
                    // Scroll suave a la sección si se solicita
                    if (scrollTo) {
                        window.scrollTo({
                            top: targetSection.offsetTop - 20,
                            behavior: 'smooth'
                        });
                    }
                }
                
                // Activar el enlace correspondiente
                const targetLink = document.querySelector(`.sidebar-nav a[href="#${sectionId}"]`);
                if (targetLink) {
                    targetLink.classList.add('active');
                }
                
                // Actualizar URL
                history.replaceState(null, null, `#${sectionId}`);
            }
            
            // Hacer clic en una sección la activa
            sections.forEach(section => {
                section.addEventListener('click', function() {
                    const sectionId = this.id;
                    activateSection(sectionId, false); // No hacer scroll adicional
                });
            });
            
            // Navegación lateral con scroll suave
            navLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const sectionId = this.getAttribute('href').substring(1);
                    activateSection(sectionId, true); // Con scroll
                });
            });
            
            // Actualización automática basada en scroll
            function updateActiveLinkOnScroll() {
                let current = '';
                
                sections.forEach(section => {
                    const sectionTop = section.offsetTop;
                    const sectionHeight = section.clientHeight;
                    if (scrollY >= (sectionTop - 200)) { // Margen mayor para mejor UX
                        current = section.getAttribute('id');
                    }
                });
                
                if (current) {
                    // Solo actualizar clases, no hacer scroll
                    sections.forEach(section => {
                        section.classList.remove('active');
                        if (section.id === current) {
                            section.classList.add('active');
                        }
                    });
                    
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === '#' + current) {
                            link.classList.add('active');
                        }
                    });
                }
            }
            
            // Escuchar eventos de scroll
            let scrollTimeout;
            window.addEventListener('scroll', function() {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(updateActiveLinkOnScroll, 100);
            });
            
            // Activar sección inicial basada en URL hash o primera sección
            const initialHash = window.location.hash.substring(1);
            if (initialHash && document.getElementById(initialHash)) {
                setTimeout(() => {
                    activateSection(initialHash, true);
                }, 100);
            } else {
                // Activar primera sección por defecto
                if (sections.length > 0) {
                    sections[0].classList.add('active');
                    const firstLink = document.querySelector(`.sidebar-nav a[href="#${sections[0].id}"]`);
                    if (firstLink) {
                        firstLink.classList.add('active');
                    }
                }
            }
            
            // Inicializar también las pestañas internas
            setTimeout(() => {
                // Pestañas de publicaciones
                const pubTabs = document.querySelectorAll('.publication-tab');
                pubTabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const year = this.getAttribute('data-year');
                        
                        // Hide all publication contents
                        document.querySelectorAll('.publication-content').forEach(content => {
                            content.style.display = 'none';
                        });
                        
                        // Remove active class from all publication tabs
                        pubTabs.forEach(t => t.classList.remove('active'));
                        
                        // Show selected content and mark tab as active
                        document.getElementById('pub-' + year).style.display = 'block';
                        this.classList.add('active');
                    });
                });
                
                // Pestañas de cursos
                const courseTabs = document.querySelectorAll('.course-tab');
                courseTabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const year = this.getAttribute('data-year');
                        
                        // Hide all course contents
                        document.querySelectorAll('.course-content').forEach(content => {
                            content.style.display = 'none';
                        });
                        
                        // Remove active class from all course tabs
                        courseTabs.forEach(t => t.classList.remove('active'));
                        
                        // Show selected content and mark tab as active
                        document.getElementById('courses-' + year).style.display = 'block';
                        this.classList.add('active');
                    });
                });
                
                // Pestañas de presentaciones
                const presTabs = document.querySelectorAll('.presentation-tab');
                presTabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const year = this.getAttribute('data-year');
                        
                        // Hide all presentation contents
                        document.querySelectorAll('.presentation-content').forEach(content => {
                            content.style.display = 'none';
                        });
                        
                        // Remove active class from all presentation tabs
                        presTabs.forEach(t => t.classList.remove('active'));
                        
                        // Show selected content and mark tab as active
                        document.getElementById('presentations-' + year).style.display = 'block';
                        this.classList.add('active');
                    });
                });
            }, 200);
        });
        </script>
        """
    
    def copy_assets(self):
        """Copy all required static assets"""
        # Copy CSS
        if os.path.exists(self.config['CSS_FILE']):
            shutil.copy2(self.config['CSS_FILE'], self.config['OUTPUT_DIR'])
        else:
            print(f"⚠️ CSS file not found: {self.config['CSS_FILE']}")
        
        # Copy profile image if exists
        profile_img_src = os.path.join(self.config['IMG_DIR'], "photo_opt3.jpeg")
        if os.path.exists(profile_img_src):
            os.makedirs(os.path.join(self.config['OUTPUT_DIR'], "imgs"), exist_ok=True)
            shutil.copy2(profile_img_src, os.path.join(self.config['OUTPUT_DIR'], "imgs"))
        else:
            print(f"⚠️ Profile image not found: {profile_img_src}")

if __name__ == "__main__":
    builder = SiteBuilder(CONFIG)
    builder.build_site()
