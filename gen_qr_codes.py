import argparse
import os
import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFont
from PIL.Image import Resampling
from PyPDF4 import PdfFileMerger
from itertools import islice


# Command Line Arguments:

parser = argparse.ArgumentParser(description='Generate n QR Codes starting with the number s.')
parser.add_argument('starting_num', metavar='s', type=int,
                    help='The identifying number for the first qr code, e.g. 100 results in the series 100, 101, 102...')
parser.add_argument('total_qr_codes', metavar='n', type=int,
                    help='How many total QR codes to generate, e.g. 10 will create ten QR codes.')
args = parser.parse_args()
starting_num = args.starting_num
total_qr_codes = args.total_qr_codes


# Constants:

# Print resolution for good quality 8.5x11 printing is 2550px W x 3300px H. (300 Pixels per Inch)
# For excellent print quality, set the resolution of your 8.5x11 artwork at 3400px x 4400px.
PDF_SIZE = (2550, 3300)
BLEED = 120
HORZ_SPACING_BETWEEN_QR_CODES = 20
VERT_SPACING_BETWEEN_QR_CODES = 20

ORIGINAL_QR_SIZE_IN_PIXELS = (290, 290)
QR_CODE_SIZE_MULTIPLIER = 1.5
QR_SIZE = (
    int(ORIGINAL_QR_SIZE_IN_PIXELS[0] * QR_CODE_SIZE_MULTIPLIER),
    int(ORIGINAL_QR_SIZE_IN_PIXELS[1] * QR_CODE_SIZE_MULTIPLIER)
)

INDIVIDUAL_PAGES_DIR = "individual_pages"
FONT_SIZE = 40
FONT = ImageFont.truetype("Roboto-Regular.ttf", FONT_SIZE)


def create_qr_code_image_objects():
    """Returns a generator of qr code PIL ImageDraw objects."""

    for i in range(total_qr_codes):
        curr_num = starting_num + i

        # Generate qr code.
        data = str(curr_num)
        qr_code_img = qrcode.make(data)
        qr_code_img = qr_code_img.resize(QR_SIZE, resample=Resampling.BOX)

        # Add text to the qr code (attempt to center at top)
        draw_canvas = ImageDraw.Draw(qr_code_img)
        draw_canvas.text(((QR_SIZE[0] // 2) - 20, 0), data, font=FONT)

        yield qr_code_img


def create_pdf_page_of_qr_codes(qr_code_image_generator):
    """Creates a new PIL image the size of a page, and writes as many qr codes onto it as possible.
    Returns a tuple of the PIL image and the number of qr_codes written to it.
    """

    # Create canvas for the final image with total canvas_size.
    pdf_canvas = Image.new('RGB', PDF_SIZE, color="#FFFFFF")

    pdf_width = PDF_SIZE[0] - BLEED
    pdf_height = PDF_SIZE[1] - BLEED

    # Paste as many qr codes into pdf_canvas as possible.
    row, col, idx = BLEED, BLEED, 0
    while row + QR_SIZE[0] + VERT_SPACING_BETWEEN_QR_CODES <= pdf_height:
        while col + QR_SIZE[0] + HORZ_SPACING_BETWEEN_QR_CODES <= pdf_width:
            try:
                resized_qr_code_img_obj = ImageOps.fit(next(qr_code_image_generator), QR_SIZE, Resampling.LANCZOS)
            except StopIteration:
                break
            pdf_canvas.paste(resized_qr_code_img_obj, (col, row))
            idx += 1

            col += QR_SIZE[0] + HORZ_SPACING_BETWEEN_QR_CODES

        col = BLEED
        row += QR_SIZE[1] + VERT_SPACING_BETWEEN_QR_CODES

    return pdf_canvas, idx


def save_pdfs_in_pages(qr_code_image_generator):
    """
    Writes the qr codes to files, each file a one page pdf. Fits as many qr codes in each file as possible.
    Returns a list of relative filepaths to the newly created pdf files.
    """

    # Create a directory to put individual qr PDFs.
    try:
        os.mkdir(INDIVIDUAL_PAGES_DIR)
    except OSError:
        # In this case, the directory already exists.
        pass

    pdf_filenames = []
    qr_code_num = starting_num
    while qr_code_num < starting_num + total_qr_codes:
        new_img, r_idx = create_pdf_page_of_qr_codes(qr_code_image_generator)
        pdf_out_filename = f"{INDIVIDUAL_PAGES_DIR}/qr_codes_{qr_code_num}_through_{(qr_code_num + r_idx - 1)}.pdf"
        new_img.save(pdf_out_filename)
        pdf_filenames.append(pdf_out_filename)
        qr_code_num += r_idx

    return pdf_filenames


def merge_pdfs(input_files: list, output_file: str):
    """
    Merge a list of PDF files and save the combined result into the `output_file`.
    """
    # Note: `strict = False` ignores PdfReadError - Illegal Character error
    merger = PdfFileMerger(strict=False)
    for input_file in input_files:
        merger.append(fileobj=open(input_file, 'rb'))

    # Insert the pdf at specific page
    merger.write(fileobj=open(output_file, 'wb'))
    merger.close()


def generate_qr_codes():
    """Main driver function."""

    # STEP 1: get a generator of qr codes...
    qr_code_image_generator = create_qr_code_image_objects()

    # STEP 2: save the qr codes into individual page pdf files...
    individual_pdf_filenames = save_pdfs_in_pages(qr_code_image_generator)

    # STEP 3: merge all the individual pdfs into one pdf of multiple pages...
    output_filename = f"qr_codes_{starting_num}_through_{(starting_num + total_qr_codes - 1)}.pdf"
    merge_pdfs(individual_pdf_filenames, output_filename)


generate_qr_codes()
