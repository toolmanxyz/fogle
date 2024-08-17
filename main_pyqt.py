import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import QThread, Qt
import mss
from PIL import Image, ImageDraw
from pynput import mouse

class ScreenshotThread(QThread):
    def __init__(self, monitor_index):
        super().__init__()
        self.monitor_index = monitor_index
        self.screenshot_count = 0  # Initialize screenshot counter
        self.listener = None

        # Load and rotate the overlay image 90 degrees clockwise
        self.overlay_image = Image.open("image.png").convert("RGBA").rotate(-90, expand=True)
        
        # Precompute the circle image
        self.circle_radius = 75
        self.circle_image = self.create_circle_image(self.circle_radius)

    def create_circle_image(self, radius):
        size = (radius * 2, radius * 2)
        circle_img = Image.new("RGBA", size)
        draw = ImageDraw.Draw(circle_img)
        draw.ellipse((0, 0, size[0], size[1]), fill=(255, 255, 0, 128))  # Yellow with 50% transparency
        return circle_img

    def run(self):
        # Start listening for mouse clicks
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        self.listener.join()

    def stop_listeners(self):
        if self.listener is not None:
            self.listener.stop()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.screenshot_count += 1  # Increment the screenshot counter
            self.take_screenshot_with_image(int(x), int(y))

    def take_screenshot_with_image(self, x, y):
        with mss.mss() as sct:
            monitor_info = sct.monitors[self.monitor_index + 1]
            scale_factor = sct.grab(monitor_info).width / monitor_info['width']

            # Capture the entire screen
            screenshot = sct.grab(monitor_info)
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')

            # Apply scale factor to coordinates
            x = int((x - monitor_info['left']) * scale_factor)
            y = int((y - monitor_info['top']) * scale_factor)

            # Paste the precomputed circle image at the click location
            img.paste(self.circle_image, (x - self.circle_radius, y - self.circle_radius), self.circle_image)

            # Adjust the position for the rotated overlay image
            position = (x - self.overlay_image.width // 2, y - self.overlay_image.height // 2 + (self.circle_radius // 2))
            img.paste(self.overlay_image, position, self.overlay_image)

            # Save the screenshot with the format screenshot_X.png
            screenshot_file = f"screenshot_{self.screenshot_count}.png"
            img.save(screenshot_file)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.screenshot_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Monitor Selection')

        # Set the window to be always on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        label = QLabel("Select Monitor:")
        layout.addWidget(label)

        self.monitor_dropdown = QComboBox(self)
        self.monitor_dropdown.addItems(self.get_monitors())
        layout.addWidget(self.monitor_dropdown)

        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.clicked.connect(self.start_screenshot_thread)
        layout.addWidget(self.confirm_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def get_monitors(self):
        with mss.mss() as sct:
            monitors = sct.monitors[1:]  # Exclude the combined all-monitors view
            return [f"Monitor {i+1} (W: {monitor['width']}, H: {monitor['height']})"
                    for i, monitor in enumerate(monitors)]

    def start_screenshot_thread(self):
        monitor_index = self.monitor_dropdown.currentIndex()

        # Start the screenshot thread
        self.screenshot_thread = ScreenshotThread(monitor_index)
        self.screenshot_thread.start()

        # Update the UI to show only the Stop button
        self.update_to_stop_button()

    def update_to_stop_button(self):
        # Clear the layout
        layout = self.centralWidget().layout()
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)

        # Add the Stop button
        stop_button = QPushButton("Stop", self)
        stop_button.clicked.connect(self.stop_program)
        layout.addWidget(stop_button)

    def stop_program(self):
        if self.screenshot_thread is not None:
            self.screenshot_thread.stop_listeners()
        QApplication.quit()  # Close the application

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())