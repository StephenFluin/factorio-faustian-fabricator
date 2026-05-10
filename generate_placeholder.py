from PIL import Image, ImageDraw

def create_placeholder(path, size, color, text):
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple box with a border
    draw.rectangle([0, 0, size[0]-1, size[1]-1], fill=color, outline=(255, 255, 255))
    draw.text((size[0]//4, size[1]//3), text, fill=(255, 255, 255))
    
    img.save(path)

# Icon: 64x64
create_placeholder("graphics/icons/faustian-fabricator.png", (64, 64), (100, 50, 150), "FF")

# Entity: 214x190 (based on data.lua)
create_placeholder("graphics/entity/faustian-fabricator.png", (214, 190), (100, 50, 150), "FAUSTIAN FABRICATOR")
