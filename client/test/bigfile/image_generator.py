from PIL import Image
import os

# Size in pixels
width, height = 4000, 4000  # 16 MP, plenty big for testing chunking
output_path = "big_test_image.png"

# Create a gradient image
img = Image.new("RGB", (width, height))
for x in range(width):
    for y in range(height):
        img.putpixel((x, y), (x % 256, y % 256, (x*y) % 256))

img.save(output_path)
print(f"Saved {output_path}, size: {os.path.getsize(output_path)} bytes")