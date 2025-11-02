import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# import operations
from operations.basic_ops import to_grayscale, invert_image
from operations.filtering import blur_image
from operations.transform import rotate_image

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Pengolahan Citra")

        self.image = None
        self.tk_image = None

        # canvas
        self.canvas = tk.Canvas(root, width=600, height=400, bg="gray")
        self.canvas.pack()

        # menu bar
        menu_bar = tk.Menu(root)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save As", command=self.save_image)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Basic operations
        basic_menu = tk.Menu(menu_bar, tearoff=0)
        basic_menu.add_command(label="Grayscale", command=self.apply_grayscale)
        basic_menu.add_command(label="Invert", command=self.apply_invert)
        menu_bar.add_cascade(label="Basic", menu=basic_menu)

        # Filtering
        filter_menu = tk.Menu(menu_bar, tearoff=0)
        filter_menu.add_command(label="Blur", command=self.apply_blur)
        menu_bar.add_cascade(label="Filter", menu=filter_menu)

        # Transform
        transform_menu = tk.Menu(menu_bar, tearoff=0)
        transform_menu.add_command(label="Rotate 90°", command=self.apply_rotate)
        menu_bar.add_cascade(label="Transform", menu=transform_menu)

        root.config(menu=menu_bar)

    def open_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.image = Image.open(path)
            self.show_image()

    def save_image(self):
        if self.image:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                self.image.save(path)

    def show_image(self):
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(300, 200, image=self.tk_image)

    # MENU OPERATIONS:
    def apply_grayscale(self):
        if self.image:
            self.image = to_grayscale(self.image)
            self.show_image()

    def apply_invert(self):
        if self.image:
            self.image = invert_image(self.image)
            self.show_image()

    def apply_blur(self):
        if self.image:
            self.image = blur_image(self.image)
            self.show_image()

    def apply_rotate(self):
        if self.image:
            self.image = rotate_image(self.image, 90)
            self.show_image()

root = tk.Tk()
app = ImageApp(root)
root.mainloop()
