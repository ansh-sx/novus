from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import textwrap
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
        current_height = 50  # Starting y-coordinate for text
        line_spacing = 10  # Space between lines

        # Load fonts
        try:
            font = ImageFont.truetype(font_path, font_size)
            bold_font = ImageFont.truetype(bold_font_path, font_size)
        except IOError as e:
            return {"error": f"Font file not found or cannot be loaded: {str(e)}"}

        # Split the text into lines based on the character limit
        lines = page_text.split("\n")
        for line in lines:
            words = line.split(" ")
            formatted_line = ""
            bold_text = ""
            current_x = 50  # x-coordinate to place regular and bold text

            for word in words:
                if word.startswith("**") and word.endswith("**"):
                    # Render the regular part of the line first
                    if formatted_line.strip():  # If there's text before bold word
                        draw.text((current_x, current_height), formatted_line.strip(), font=font, fill="black")
                        formatted_line_width = draw.textbbox((0, 0), formatted_line.strip(), font=font)[2]
                        current_x += formatted_line_width  # Move the x position for the next part

                    # Now render the bold text
                    bold_word = word.strip("**")
                    draw.text(
                        (current_x, current_height),
                        bold_word,
                        font=bold_font,
                        fill="black",
                    )
                    # Update current_x after drawing the bold text
                    bold_word_width = draw.textbbox((0, 0), bold_word, font=bold_font)[2]
                    current_x += bold_word_width  # Move the x position after bold text
                    formatted_line = ""  # Reset regular text after processing bold word
                else:
                    formatted_line += word + " "

            # After looping through all words, render the remaining regular text if any
            if formatted_line.strip():
                draw.text((current_x, current_height), formatted_line.strip(), font=font, fill="black")
                current_x += draw.textbbox((0, 0), formatted_line.strip(), font=font)[2]

            # Update the current height for the next line
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

    font_path = "t.ttf"  # Font file in the root folder
    bold_font_path = "tb.ttf"  # Font file in the root folder
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
