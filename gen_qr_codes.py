# Importing the PIL library

import qrcode
from PIL import Image, ImageDraw, ImageOps, ImageFont
from PIL.Image import Resampling

# Parameters:

# Print resolution for good quality 8.5x11 printing is 2550px W x 3300px H. (300 Pixels per Inch)
# For excellent print quality, set the resolution of your 8.5x11 artwork at 3400px x 4400px.
pdf_size = (2550, 3300)
bleed = 70

starting_num = 100001
num_qr_codes = 50

orig_qr_size_in_pixels = (290, 290)
qr_size_multiplier = 1.5
font_size = 40


# Code:
fnt = ImageFont.truetype("Roboto-Regular.ttf", font_size)

def concat_images(images, start_idx=0):
    images = images[start_idx:]

    # Open images and resize them
    width, height = pdf_size
    images = [ImageOps.fit(image, qr_size, Resampling.LANCZOS)
              for image in images]

    # Create canvas for the final image with total canvas_size
    # shape = shape if shape else (1, len(images))
    # image_size = (width * shape[1], height * shape[0])
    pdf_canvas = Image.new('RGB', (width, height), color="#FFFFFF")

    pdf_width = width - bleed
    pdf_height = height - bleed

    # Paste images into final image
    row, col, idx = bleed, bleed, 0
    while row + qr_size[0] <= pdf_height and idx < len(images):
        while col + qr_size[0] <= pdf_width and idx < len(images):
            pdf_canvas.paste(images[idx], (col, row))
            idx += 1

            if col + qr_size[0] + qr_size[0] < pdf_width:
                col += qr_size[0]
            else:
                col = bleed
                row += qr_size[1]
                break

    return pdf_canvas, idx


def gen_list_qr_codes():
    r = []

    for i in range(num_qr_codes):
        curr_num = starting_num + i

        # generate qr code
        data = str(curr_num)
        qr_code_img = qrcode.make(data)
        qr_code_img = qr_code_img.resize(qr_size, resample=Resampling.BOX)

        # save img to a file
        # qr_code_img.save('filename')

        # Call draw Method to add 2D graphics in an image
        i1 = ImageDraw.Draw(qr_code_img)

        # Add text to the qr code (attempt to center at top)
        i1.text(((qr_size[0] // 2) - 60, 0), data, font=fnt)

        r.append(qr_code_img)

    return r

# get a font

qr_size = (
    int(orig_qr_size_in_pixels[0] * qr_size_multiplier),
    int(orig_qr_size_in_pixels[1] * qr_size_multiplier)
)
qr_images_list = gen_list_qr_codes()

pdf_out_num = 0
idx = 0
while idx < num_qr_codes:
    new_img, r_idx = concat_images(qr_images_list, idx)
    idx += r_idx
    new_img.save(f"new_grid{pdf_out_num}.pdf")
    pdf_out_num += 1
