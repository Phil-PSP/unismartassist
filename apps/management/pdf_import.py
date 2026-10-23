"""
PDF Student Import — parses KAAF University attendance/class list PDFs.

Expected format (from portal.kaafuni.edu.gh):
  Header: Department of X, Level: NNN, AcademicYear: YYYY/YYYY, Semester: Nth Semester
  Table:  No | Student No | Student Name
  Names are ALL CAPS, surname first: "AWUNI MARGARET"
  Student No is 8 digits: "11100523"
"""
import re


def extract_text_from_pdf(file_obj):
    """Extract all text from a PDF using pdfplumber."""
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                # Try table extraction first (more structured)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if row:
                                pages.append('\t'.join(str(c or '').strip() for c in row))
                # Always also grab raw text for header parsing
                t = page.extract_text()
                if t:
                    pages.append(t)
        return '\n'.join(pages)
    except Exception as e:
        raise ValueError(f"Could not read PDF: {e}")


def parse_header(text):
    """
    Extract metadata from the PDF header.
    Returns dict: {department, level, academic_year, semester, programme_code}
    """
    meta = {
        'department': '',
        'level': None,
        'academic_year': '2025/2026',
        'semester': 1,
        'programme_code': '',
    }

    # Department: "Department of Accounting"
    m = re.search(r'Department\s+of\s+(.+)', text, re.IGNORECASE)
    if m:
        meta['department'] = m.group(1).strip().title()

    # Level: "Level: 300" or "Level:300"
    m = re.search(r'Level\s*[:\-]?\s*(\d{3})', text, re.IGNORECASE)
    if m:
        meta['level'] = int(m.group(1))

    # Academic Year: "AcademicYear: 2025/2026" or "Academic Year: 2025/2026"
    m = re.search(r'Academic\s*Year\s*[:\-]?\s*(\d{4}/\d{4})', text, re.IGNORECASE)
    if m:
        meta['academic_year'] = m.group(1)

    # Semester: "2nd Semester" → 2, "1st Semester" → 1
    m = re.search(r'(\d+)(?:st|nd|rd|th)\s+Semester', text, re.IGNORECASE)
    if m:
        meta['semester'] = int(m.group(1))

    # Programme code from URL: "programme=BAC"
    m = re.search(r'programme=([A-Z]+)', text)
    if m:
        meta['programme_code'] = m.group(1)

    return meta


def parse_students_from_text(text, default_level=100, default_programme=None):
    """
    Parse student rows from KAAF PDF text.
    Returns list of dicts: {student_no, first_name, last_name, level, programme_hint, academic_year, semester}
    """
    meta = parse_header(text)
    level = meta['level'] or default_level
    academic_year = meta['academic_year']
    semester = meta['semester']
    department = meta['department']
    programme_code = meta['programme_code']

    students = []
    seen_ids = set()

    lines = text.splitlines()
    for line in lines:
        line = line.strip()

        # Match: optional number, tab/spaces, 8-digit student no, tab/spaces, NAME IN CAPS
        # Handles both table-extracted (tab-separated) and raw text
        m = re.match(
            r'(?:\d+\s*[\t|]?\s*)?'           # optional row number
            r'(\d{7,10})'                       # student number (7-10 digits)
            r'[\s\t|]+'                         # separator
            r'([A-Z][A-Z\s\'\-\.]{2,60})',     # name in CAPS
            line
        )
        if not m:
            continue

        student_no = m.group(1).strip()
        raw_name = m.group(2).strip()

        # Skip header row
        if raw_name.upper() in ('STUDENT NAME', 'NAME', 'FULL NAME'):
            continue

        # Skip duplicates
        if student_no in seen_ids:
            continue
        seen_ids.add(student_no)

        # Clean name — remove trailing junk
        raw_name = re.sub(r'\s{2,}.*$', '', raw_name).strip()
        words = raw_name.split()
        if len(words) < 2:
            continue

        # KAAF format: SURNAME FIRSTNAME [OTHERNAME]
        # Convert to title case
        last_name = words[0].capitalize()
        first_name = ' '.join(w.capitalize() for w in words[1:])

        students.append({
            'student_no': student_no,
            'first_name': first_name,
            'last_name': last_name,
            'level': level,
            'academic_year': academic_year,
            'semester': semester,
            'department': department,
            'programme_code': programme_code,
            'programme_hint': department or (default_programme or ''),
        })

    return students, meta


def find_programme(hint, programme_code, all_programmes):
    """Match department name or programme code to a Programme object."""
    if not hint and not programme_code:
        return None

    # Try exact code match first
    if programme_code:
        for prog in all_programmes:
            if prog.code.upper() == programme_code.upper():
                return prog

    # Try name match
    if hint:
        hint_lower = hint.lower()
        for prog in all_programmes:
            if hint_lower in prog.name.lower() or prog.name.lower() in hint_lower:
                return prog
        # Partial word match
        for prog in all_programmes:
            for word in hint_lower.split():
                if len(word) > 4 and word in prog.name.lower():
                    return prog

    return None


def generate_email(first_name, last_name, student_no):
    """Generate institutional student email from student number."""
    return f"{student_no}@qhophietornam.kaafuni.edu.gh"
