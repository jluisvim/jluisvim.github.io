# Academic Website Generator

A Python script to generate a professional academic website from structured data files.

## Features

- Generates a complete academic website from structured data
- Supports publications, presentations, teaching activities, and news updates
- Responsive design with clean typography
- Automatic statistics generation
- Year-based filtering for publications and presentations

## Input Files

The script requires the following input files:

1. **Bibliographic Data**:
   - `mybiblio.bib`: BibTeX file containing your publications

2. **CSV Data Files**:
   - `courses.csv`: Teaching activities with columns:
     - `Academic Year`, `Institution`, `Lecture Type`, `Lecture Name`, `Duration`
   - `presentations.csv`: Academic presentations with columns:
     - `Año` (Year), `Mes` (Month), `Evento` (Event), `Título` (Title), `Lugar` (Location), `Autores` (Authors)
   - `news.csv`: News/updates with columns:
     - `date` (YYYY-MM-DD), `event`, `link` (optional)

3. **Template File**:
   - `template_base.html`: HTML template containing placeholders for dynamic content

4. **Assets**:
   - `styles.css`: CSS stylesheet
   - `imgs/photo_opt3.jpeg`: Profile photo (optional)

## Output Files

The script generates:

1. `dist/index.html`: Complete website HTML file
2. `dist/styles.css`: Copied CSS stylesheet
3. `dist/imgs/`: Directory containing profile photo (if provided)

## Configuration

Edit the `CONFIG` dictionary in the script to:

- Set file paths
- Define author name variants for highlighting
- Map research domains
- Configure other display options

## Usage

1. Install required dependencies:
   ```bash
   pip install bibtexparser
