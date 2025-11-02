import tkinter as tk
from tkinter import filedialog, Toplevel, Scale, HORIZONTAL, messagebox
from PIL import Image, ImageTk

from operations.basic_ops import to_grayscale, invert_image, adjust_brightness, adjust_contrast
from operations.filtering import blur_image, sharpen_image, gaussian_blur
from operations.transform import rotate_image, resize_image
from operations.edge_detection import edge_simple


class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Pengolahan Citra")

        self.image = None
        self.preview_image = None
        self.display_image = None

        # Undo & Redo Stack
        self.history = []
        self.future = []   # redo stack

        # Canvas
        self.canvas = tk.Canvas(root, width=700, height=500, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        # ==========================
        # MENU BAR (Undo + Redo)
        # ==========================
        menu_bar = tk.Menu(root)

        # Undo & Redo — simbol saja
        menu_bar.add_command(label="↶", command=self.undo)
        menu_bar.add_command(label="↷", command=self.redo)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save As", command=self.save_image)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Basic Ops
        basic_menu = tk.Menu(menu_bar, tearoff=0)
        basic_menu.add_command(label="Grayscale", command=self.apply_grayscale)
        basic_menu.add_command(label="Invert", command=self.apply_invert)
        basic_menu.add_command(label="Brightness", command=self.slider_brightness)
        basic_menu.add_command(label="Contrast", command=self.slider_contrast)
        menu_bar.add_cascade(label="Basic", menu=basic_menu)

        # Filter Menu
        filter_menu = tk.Menu(menu_bar, tearoff=0)
        filter_menu.add_command(label="Blur", command=self.apply_blur)
        filter_menu.add_command(label="Gaussian Blur", command=self.slider_gaussian)
        filter_menu.add_command(label="Sharpen", command=self.apply_sharpen)
        menu_bar.add_cascade(label="Filter", menu=filter_menu)

        # Transform Menu
        transform_menu = tk.Menu(menu_bar, tearoff=0)
        transform_menu.add_command(label="Rotate", command=self.slider_rotate)
        transform_menu.add_command(label="Resize", command=self.slider_resize)
        menu_bar.add_cascade(label="Transform", menu=transform_menu)

        # Edge Menu
        edge_menu = tk.Menu(menu_bar, tearoff=0)
        edge_menu.add_command(label="Edge Detect", command=self.apply_edge)
        menu_bar.add_cascade(label="Edge", menu=edge_menu)

        root.config(menu=menu_bar)

    # ==========================
    # FILE HANDLING
    # ==========================
    def open_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.image = Image.open(path)
            self.history.clear()
            self.future.clear()
            self.show_image()

    def save_image(self):
        if not self.image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            self.image.save(path)

    # ==========================
    # UNDO / REDO SYSTEM
    # ==========================
    def save_state(self):
        """Save current state before modification."""
        if self.image:
            self.history.append(self.image.copy())
            self.future.clear()  # clear redo stack after new action

    def undo(self):
        if not self.history:
            messagebox.showinfo("Undo", "Tidak ada aksi sebelumnya.")
            return

        self.future.append(self.image.copy())     # push current state to redo stack
        self.image = self.history.pop()           # revert to last history
        self.show_image()

    def redo(self):
        if not self.future:
            messagebox.showinfo("Redo", "Tidak ada aksi untuk diulang.")
            return

        self.history.append(self.image.copy())    # current goes to history
        self.image = self.future.pop()            # get redo state
        self.show_image()

    # ==========================
    # DISPLAY IMAGE
    # ==========================
    def show_image(self, img=None):
        if img is None:
            img = self.image
        if img is None:
            return

        show = img.copy()
        show.thumbnail((900, 700))
        self.display_image = ImageTk.PhotoImage(show)

        self.canvas.delete("all")
        self.canvas.create_image(450, 350, image=self.display_image)

    # ==========================
    # BASIC OPS
    # ==========================
    def apply_grayscale(self):
        self.save_state()
        self.image = to_grayscale(self.image)
        self.show_image()

    def apply_invert(self):
        self.save_state()
        self.image = invert_image(self.image)
        self.show_image()

    # ==========================
    # SLIDER PREVIEW SYSTEM
    # ==========================
    def create_slider_window(self, title, preview_func):
        win = Toplevel(self.root)
        win.title(title)
        win.geometry("350x120")

        slider = Scale(win, from_=1, to=100, orient=HORIZONTAL)
        slider.pack(fill="x", padx=20, pady=10)

        def update_preview(value):
            self.preview_image = preview_func(float(value))
            self.show_image(self.preview_image)

        slider.configure(command=update_preview)

        def apply_action():
            self.save_state()
            self.image = self.preview_image.copy()
            self.show_image()
            win.destroy()

        tk.Button(win, text="Apply", command=apply_action).pack(pady=5)

    # ==========================
    # BRIGHTNESS & CONTRAST
    # ==========================
    def slider_brightness(self):
        self.create_slider_window(
            "Brightness",
            lambda v: adjust_brightness(self.image, v / 33)
        )

    def slider_contrast(self):
        self.create_slider_window(
            "Contrast",
            lambda v: adjust_contrast(self.image, v / 33)
        )

    # ==========================
    # FILTERING
    # ==========================
    def apply_blur(self):
        self.save_state()
        self.image = blur_image(self.image)
        self.show_image()

    def slider_gaussian(self):
        self.create_slider_window(
            "Gaussian Blur",
            lambda v: gaussian_blur(self.image, int(v / 10))
        )

    def apply_sharpen(self):
        self.save_state()
        self.image = sharpen_image(self.image)
        self.show_image()

    # ==========================
    # TRANSFORM
    # ==========================
    def slider_rotate(self):
        self.create_slider_window(
            "Rotate",
            lambda v: rotate_image(self.image, int(v * 3.6))
        )

    def slider_resize(self):
        win = Toplevel(self.root)
        win.title("Resize")
        win.geometry("350x200")

        w0, h0 = self.image.size

        w_slider = Scale(win, from_=1, to=100, orient=HORIZONTAL, label="Width (%)")
        h_slider = Scale(win, from_=1, to=100, orient=HORIZONTAL, label="Height (%)")
        w_slider.pack(fill="x", padx=20)
        h_slider.pack(fill="x", padx=20)

        w_slider.set(100)
        h_slider.set(100)

        def preview(value):
            w = int(w0 * (w_slider.get() / 100))
            h = int(h0 * (h_slider.get() / 100))
            self.preview_image = resize_image(self.image, w, h)
            self.show_image(self.preview_image)

        w_slider.configure(command=preview)
        h_slider.configure(command=preview)

        def apply():
            self.save_state()
            self.image = self.preview_image.copy()
            self.show_image()
            win.destroy()

        tk.Button(win, text="Apply", command=apply).pack(pady=5)

    # ==========================
    # EDGE DETECTION
    # ==========================
    def apply_edge(self):
        self.save_state()
        self.image = edge_simple(self.image)
        self.show_image()


root = tk.Tk()
app = ImageApp(root)
root.mainloop()
