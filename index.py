__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import base64

app = Flask(__name__)

# Function to generate images for a chapter using existing images
def generate_images(image_index, chapter_text, font_path, bold_font_path, font_size, char_limit_per_line=100, char_limit_per_page=800):
    output_images = []
    pages = []

    # Wrap the text based on the character limit per page
    page_text = textwrap.wrap(chapter_text, char_limit_per_page)
    page_number = 1

    # Fixed background size
    image_width, image_height = 1080, 1920  # width: 1080px, height: 1920px (portrait)

    for page in page_text:
        # Load the existing image (e.g., "1.jpg", "2.jpg")
        image_path = f"{image_index}.jpg"
        
        if not os.path.exists(image_path):
            return {"error": f"Image {image_index}.jpg not found in the root folder."}

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

        # Split the page text into lines based on the character limit per line
        lines = textwrap.wrap(page, char_limit_per_line)
        
        for line in lines:
            words = line.split(" ")
            formatted_line = ""
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

            # Check if the current height exceeds the page height, meaning we need a new page
            if current_height + font_size + line_spacing > image_height:
                # Save the image to a BytesIO object instead of writing to a file
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr.seek(0)  # Go to the beginning of the byte array
                output_images.append(base64.b64encode(img_byte_arr.read()).decode('utf-8'))
                page_number += 1
                image_index += 1  # Move to the next image
                img = Image.open(f"{image_index}.jpg")  # Load the next image
                draw = ImageDraw.Draw(img)
                current_height = 50  # Reset the y-coordinate for the next page

        # Save the final page if it's not empty
        if current_height > 50:  # If there's any content on the last page
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)  # Go to the beginning of the byte array
            output_images.append(base64.b64encode(img_byte_arr.read()).decode('utf-8'))

    return output_images


@app.route("/generate-chapter", methods=["POST"])
def generate_chapter():
    data = request.json
    image_index = int(data.get("image"))  # Index of the image template (e.g., "1")
    chapter_text = data.get("chapter")  # Chapter text

    font_path = "t.ttf"  # Regular font file in the root folder
    bold_font_path = "tb.ttf"  # Bold font file in the root folder
    font_size = 24
    char_limit_per_line = 100  # Max characters per line
    char_limit_per_page = 800  # Max characters per page

    try:
        images = generate_images(image_index, chapter_text, font_path, bold_font_path, font_size, char_limit_per_line, char_limit_per_page)

        # Return the images as a response
        return jsonify({"pages": len(images), "images": images})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
