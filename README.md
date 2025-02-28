# pdf-outline
Example files for applying bookmarks to an existing PDF with pdflatex

## Instructions
To apply the bookmarks, after you've mapped section titles to the desired pages and nesting levels:

- replace `your.pdf` in the line `\includepdf[pages=1-]{your.pdf}` with the name of your original PDF
  - you may want to remove spaces in the PDF title
- place your original PDF in the present working directory with `your.tex` file
- run `pdflatex your.tex`
  - you may want to append `1>/dev/null` to the command if it spams unwanted pdfTeX warnings
- you should then see `your.pdf` in your pwd
