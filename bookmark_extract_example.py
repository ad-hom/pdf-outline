#!/usr/bin/env python3
import re
import os
import argparse
from html import unescape
from unicodedata import normalize
from itertools import chain

# This script generates a template LaTeX file with bookmarks for a particular
# PDF document. Using it will require some manual adjustments to the patterns
# used to extract chapter and section titles, as well as those used to find the
# correct page numbers.
#
# Before attempting to run the script, get the HTML content from a PDF textbook
# with the following command. For example:
#   ```
#   pdftohtml -i -s -stdout Programming\ in\ Ada\ 2012\ \(Barnes\,\ 2014\).pdf \
#   | sed 's/&#160;/ /g' > temp.html`
#   ```
# The sed command replaces non-breaking spaces with regular spaces.

def extract_bookmarks_from_html(html_content):
    """Extract chapter and section records from HTML content."""
    # Extract chapters and appendicies
    chapter_pattern = r'</p>\n<p [^>]+"><b>(A?\d+)</b></p>\n<p [^>]+"><b>(\w[^<]+)</b></p>\n<p [^>]+">(\d+)'
    chapters = re.findall(chapter_pattern, html_content)

    # Extract sections for each chapter or appendix
    section_patterns = [
        r'">(\d+\.\d+)</p>\n<p [^>]+">(\w[^<]+\w)</p>\n<p [^>]+">(\d+)</p>',
        r'">(A\d+\.\d+) (\w[\w ]+)</p>\n<p [^>]+">(\d+)</p>'
    ]
    # combine search results into a single list
    sections = list(chain.from_iterable([re.findall(p, html_content) for p in section_patterns]))

    print(f"Initially found {len(chapters)} chapters and {len(sections)} sections")
    return chapters, sections

def find_match_page(html_content, num, title, page, base_pattern, result_offset=0):
    # Update the chapter or section page number if the associated pattern is found
    filled_pattern = base_pattern.format(
        num=num,
        title=title,
        page=page
    )
    match = re.search(filled_pattern, html_content)
    if match:
        page_found = match.string[:match.start()].count('</div>') + result_offset
        print(f"Updated page for {num}: {title} - Page {page} -> {page_found}")
        return page_found
    else:
        # If no match found, section is probably not in the HTML,
        # so print but do nothing
        print(f"Could not update page for {num}: {title}")
        return

def update_chapter_pages(html_content, chapters):
    """Update page number for each chapter by locating its first page header."""
    updated_chapters = []

    for chapter_num, chapter_title, initial_page in chapters:
        # Search for the first chapter heading,
        # after the start of the chapter
        next_page = int(initial_page) + 1
        # Convert special characters in title extracted from TOC with regular text
        # 'NFKC' normalization improves handling of Unicode whitespace variants
        chapter_title = normalize('NFKC', unescape(chapter_title))
        base_pattern = '(?i:<b>{page}</b></p>\\n<p [^>]+">{title}</p>\\n<)'
        page_found = find_match_page(
            html_content,
            chapter_num,
            chapter_title,
            next_page,
            base_pattern
        )
        if page_found:
            updated_chapters.append((chapter_num, chapter_title, page_found))

    return updated_chapters

def update_section_pages(html_content, sections):
    """Update page number for each section by locating its first body header."""
    updated_sections = []

    for section_num, section_title, initial_page in sections:
        # Search pattern for this section
        # Convert special characters in title to regular text
        # 'NFKC' normalization improves handling of Unicode whitespace variants
        section_title = normalize('NFKC', unescape(section_title))
        # Found a typo in the text
        section_title = section_title.replace('specifictions', 'specifications')
        base_pattern = '(?i:><b>{num}</b></p>\\n<p [^>]+"><b>[^>]*{title}[^>]*</b>)'
        page_found = find_match_page(
            html_content,
            section_num,
            section_title,
            initial_page,
            base_pattern,
            result_offset=1
        )
        if page_found:
            # Count the pages before the match
            updated_sections.append((section_num, section_title, page_found))

    return updated_sections

def generate_tex_file(chapters, sections, output_file):
    """Generate a .tex file with bookmarks for the PDF."""
    # LaTeX document preamble
    tex_content = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{pdfpages}
\usepackage[
  pdfpagelabels=true,
  pdftitle={Title of the PDF},
  pdfauthor={Name of the Author(s)},
]{hyperref}
\usepackage{bookmark}
\usepackage{comment}

\begin{comment}
  This file was automatically generated as a template.
  It includes bookmarks for chapters and sections extracted from an HTML conversion of a PDF.

  Tex code borrowed from:
  https://michaelgoerz.net/notes/pdf-bookmarks-with-latex.html

  Found by:
  https://unix.stackexchange.com/questions/3378/modifying-pdf-files/12531#12531
\end{comment}

\begin{document}

\pagenumbering{arabic}
\setcounter{page}{1}
\includepdf[pages=1-]{temp.pdf}

"""

    # Add chapter bookmarks (level 0)
    for chapter_num, chapter_title, page_num in chapters:
        tex_content += f"\\bookmark[page={page_num},level=0]{{Ch {chapter_num}: {chapter_title}}}\n"

        # Add section bookmarks (level 1)
        for section_num, section_title, page_num in sections:
            if section_num.startswith(chapter_num + '.'):
                tex_content += f"\\bookmark[page={page_num},level=1]{{Section {section_num}: {section_title}}}\n"

    # Close the document
    tex_content += r"""
\end{document}"""

    # Write to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    print(f"Generated LaTeX file with bookmarks at {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LaTeX file with bookmarks for PDF from HTML content.")
    parser.add_argument("input_file", help="Path to the input HTML file")
    parser.add_argument("-o", "--output",
                        dest="output_file",
                        default="bookmarks.tex",
                        help="Path to the output .tex file (default: bookmarks.tex)")
    args = parser.parse_args()

    # Read the input HTML file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract chapters and sections
    chapters, sections = extract_bookmarks_from_html(html_content)
    # Update chapter and section pages
    updated_chapters = update_chapter_pages(html_content, chapters)
    updated_sections = update_section_pages(html_content, sections)

    # Generate the .tex file with bookmarks
    generate_tex_file(updated_chapters, updated_sections, args.output_file)