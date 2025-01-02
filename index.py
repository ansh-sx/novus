from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import io

app = Flask(__name__)

# Function to generate images for a chapter
def generate_images(image_index, chapter_text, font_path, bold_font_path, font_size, char_limit=300):
    output_images = []
    pages = textwrap.wrap(chapter_text, char_limit)
    page_number = 1

    for page_text in pages:
        image_path = f"{image_index}.jpg"
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        current_height = 50  # Starting y-coordinate
        line_spacing = 10

        # Load fonts
        font = ImageFont.truetype(font_path, font_size)
        bold_font = ImageFont.truetype(bold_font_path, font_size)

        # Process text and split into lines
        lines = page_text.split("\n")
        for line in lines:
            words = line.split(" ")
            formatted_line = ""
            for word in words:
                if word.startswith("**") and word.endswith("**"):
                    draw.text((50, current_height), formatted_line.strip(), font=font, fill="black")
                    formatted_line = ""
                    draw.text(
                        (50 + draw.textsize(formatted_line, font=font)[0], current_height),
                        word.strip("**"),
                        font=bold_font,
                        fill="black",
                    )
                else:
                    formatted_line += word + " "

            draw.text((50, current_height), formatted_line.strip(), font=font, fill="black")
            current_height += font_size + line_spacing

        # Save the image to a buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        output_images.append(buffer)
        page_number += 1

    return output_images


@app.route("/generate-chapter", methods=["POST"])
def generate_chapter():
    data = request.json
    image_index = data.get("image")  # Index of the image template (e.g., "1")
    chapter_text = data.get("chapter")  # Chapter text

    font_path = "t.ttf"  # Regular font path
    bold_font_path = "tb.ttf"  # Bold font path
    font_size = 24
    char_limit = 300

    try:
        images = generate_images(image_index, chapter_text, font_path, bold_font_path, font_size, char_limit)

        # Return the images as a response
        response_images = []
        for i, img in enumerate(images):
            img.seek(0)
            response_images.append({"page": i + 1, "image": img.read().hex()})

        return jsonify({"pages": len(images), "images": response_images})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
