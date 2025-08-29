from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

def create_tray_image():
    image = Image.new("RGB", (64, 64), color=(76, 175, 80))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return image

def start_tray():
    icon = Icon(
        "POS Agent",
        icon=create_tray_image(),
        menu=Menu(MenuItem("Exit", lambda icon, item: icon.stop())),
    )
    icon.run()
