import os
import time
from pynput import mouse, keyboard
from PIL import Image, ImageDraw
import mss

# Create directories for saving screenshots and logs
os.makedirs("screenshots", exist_ok=True)
os.makedirs("logs", exist_ok=True)

screenshot_counter = 0
selected_monitor = 1  # Default to the primary monitor (monitor 1)
should_exit = False  # Global flag to indicate if the program should exit
image_path = "image.png"  # Path to the image to be used instead of emoji

# Function to take a screenshot and draw a circle and an image at the mouse click location
def take_screenshot_with_image(x, y, monitor, scale_factor):
    global screenshot_counter
    screenshot_counter += 1
    
    with mss.mss() as sct:
        monitor_info = sct.monitors[monitor]
        screenshot = sct.grab(monitor_info)
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        # Adjust the coordinates for the scaling factor
        x = int(x * scale_factor)
        y = int(y * scale_factor)
        
        # Draw a semi-transparent yellow circle
        draw = ImageDraw.Draw(img, 'RGBA')
        circle_radius = 75
        draw.ellipse((x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius),
                     fill=(255, 255, 0, 128))  # Yellow with 50% transparency
        
        # Load the image
        try:
            overlay_image = Image.open(image_path)
            overlay_image = overlay_image.convert("RGBA")
            
            # Calculate the position to paste the image (left-aligned with X, centered on Y)
            image_width, image_height = overlay_image.size
            position = (x, y - image_height // 2)
            
            # Paste the image onto the screenshot
            img.paste(overlay_image, position, overlay_image)
        except IOError:
            print(f"Error: Unable to open image at {image_path}")
        
        filename = f"screenshots/screenshot_{screenshot_counter}.png"
        img.save(filename)
        return filename

# Mouse listener
def on_click(x, y, button, pressed):
    if should_exit:
        return False  # Stop mouse listener
    if pressed:
        # Adjust x and y based on the selected monitor and scale factor
        with mss.mss() as sct:
            monitor_info = sct.monitors[selected_monitor]
            scale_factor = sct.grab(monitor_info).width / monitor_info['width']
            x_adjusted = x - monitor_info["left"]
            y_adjusted = y - monitor_info["top"]

        screenshot_file = take_screenshot_with_image(x_adjusted, y_adjusted, selected_monitor, scale_factor)
        log_event(f"Mouse clicked at ({x}, {y}) with {button}. Screenshot: {screenshot_file}")

# Keyboard listener
def on_press(key):
    global should_exit
    try:
        if should_exit:
            return False  # Stop keyboard listener
        log_event(f"Key {key.char} pressed")
    except AttributeError:
        if key == keyboard.Key.esc:
            print("Esc key pressed. Exiting program.")
            should_exit = True
            return False  # Stop keyboard listener
        log_event(f"Special key {key} pressed")

# Log events
def log_event(event):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open("logs/events.log", "a") as log_file:
        log_file.write(f"{timestamp} - {event}\n")
    print(f"{timestamp} - {event}")

# Allow the user to select the monitor
def select_monitor():
    global selected_monitor
    with mss.mss() as sct:
        for i, monitor in enumerate(sct.monitors[1:], start=1):  # sct.monitors[0] is all monitors combined
            print(f"Monitor {i}: {monitor}")
        selected_monitor = int(input(f"Select monitor (1-{len(sct.monitors) - 1}): "))

# Start the mouse and keyboard listeners
def start_listeners():
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    keyboard_listener.join()  # Wait for the keyboard listener to finish
    mouse_listener.stop()  # Ensure mouse listener is stopped when Esc is pressed

if __name__ == "__main__":
    print("Starting event recording... Press Ctrl+C to stop or press Esc.")
    select_monitor()
    try:
        start_listeners()
    except KeyboardInterrupt:
        print("Recording stopped.")