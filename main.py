import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk

# Import modul operasi
from operations import basic_ops as basic
from operations import enhancement as enh
from operations import filtering as filt
from operations import geometrics as geom
from operations import arithmetic as arith
from operations import boolean as boolop
from operations import noise as noise_mod
from operations import edge_detection as edge


# Helper convert PIL → Tk
def pil_to_tk(img, maxsize=(900, 700)):
    img_copy = img.copy()
    img_copy.thumbnail(maxsize, Image.LANCZOS)
    return ImageTk.PhotoImage(img_copy)


class ImageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Processing App (PCD)")
        self.geometry("1200x820")

        self.image = None
        self.image_path = None
        self.tk_image = None

        # UNDO REDO STACK
        self.history = []
        self.future = []

        self._build_ui()

    # BUILD UI
    def _build_ui(self):

        # 1) TOOLBAR 
        top_bar = tk.Frame(self, bg="#333")
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="⮪", width=4, command=self.undo).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(top_bar, text="⮫", width=4, command=self.redo).pack(side=tk.LEFT, padx=4, pady=2)

        # 2) MENU BAR 
        menubar = tk.Menu(self)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As...", command=self.save_as_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # EDGE DETECTION
        edge_menu = tk.Menu(menubar, tearoff=0)

        grad1 = tk.Menu(edge_menu, tearoff=0)
        grad1.add_command(label="Sobel", command=self._sobel)
        grad1.add_command(label="Prewitt", command=self._prewitt)
        grad1.add_command(label="Roberts", command=self._roberts)
        edge_menu.add_cascade(label="1st Differential Gradient", menu=grad1)

        grad2 = tk.Menu(edge_menu, tearoff=0)
        grad2.add_command(label="Laplacian", command=self._laplacian)
        grad2.add_command(label="LoG", command=self._log)
        grad2.add_command(label="Canny", command=self._canny)
        edge_menu.add_cascade(label="2nd Differential Gradient", menu=grad2)

        menubar.add_cascade(label="Edge Detection", menu=edge_menu)

        # BASIC OPS
        basic_menu = tk.Menu(menubar, tearoff=0)
        basic_menu.add_command(label="Negative", command=self._invert)

        # Arithmetic
        ar_menu = tk.Menu(basic_menu, tearoff=0)
        ar_menu.add_command(label="Add", command=lambda: self._arithmetic("add"))
        ar_menu.add_command(label="Subtract", command=lambda: self._arithmetic("sub"))
        ar_menu.add_command(label="Multiply", command=lambda: self._arithmetic("mul"))
        ar_menu.add_command(label="Divide", command=lambda: self._arithmetic("div"))
        basic_menu.add_cascade(label="Arithmetic", menu=ar_menu)

        # Boolean
        bool_menu = tk.Menu(basic_menu, tearoff=0)
        bool_menu.add_command(label="NOT", command=lambda: self._boolean("not"))
        bool_menu.add_command(label="AND", command=lambda: self._boolean("and"))
        bool_menu.add_command(label="OR", command=lambda: self._boolean("or"))
        bool_menu.add_command(label="XOR", command=lambda: self._boolean("xor"))
        basic_menu.add_cascade(label="Boolean", menu=bool_menu)

        # Geometrics
        geo_menu = tk.Menu(basic_menu, tearoff=0)
        geo_menu.add_command(label="Translation", command=self._translate)
        geo_menu.add_command(label="Rotation", command=self._rotate)
        geo_menu.add_command(label="Zooming", command=self._zoom)
        geo_menu.add_command(label="Flipping", command=self._flip)
        geo_menu.add_command(label="Cropping", command=self._crop)
        basic_menu.add_cascade(label="Geometrics", menu=geo_menu)

        basic_menu.add_command(label="Thresholding", command=self._thresholding)
        basic_menu.add_command(label="Convolution", command=self._convolution)
        basic_menu.add_command(label="Fourier Transform", command=self._fft)

        # Colouring
        col_menu = tk.Menu(basic_menu, tearoff=0)
        col_menu.add_command(label="Binary", command=lambda: self._convert_color("binary"))
        col_menu.add_command(label="Grayscale", command=lambda: self._convert_color("L"))
        col_menu.add_command(label="RGB", command=lambda: self._convert_color("RGB"))
        col_menu.add_command(label="HSV", command=lambda: self._convert_color("HSV"))
        col_menu.add_command(label="CMY", command=lambda: self._convert_color("CMY"))
        col_menu.add_command(label="YUV", command=lambda: self._convert_color("YUV"))
        col_menu.add_command(label="YIQ", command=lambda: self._convert_color("YIQ"))
        col_menu.add_command(label="Pseudo", command=lambda: self._convert_color("pseudo"))
        basic_menu.add_cascade(label="Colouring", menu=col_menu)

        menubar.add_cascade(label="Basic Ops", menu=basic_menu)

        # ENHANCEMENT
        enh_menu = tk.Menu(menubar, tearoff=0)
        enh_menu.add_command(label="Brightness", command=self._brightness)
        enh_menu.add_command(label="Contrast", command=self._contrast)
        enh_menu.add_command(label="Hist. Equalization", command=self._histeq)

        smoothing_menu = tk.Menu(enh_menu, tearoff=0)
        smoothing_menu.add_command(label="Gaussian Blur", command=lambda: self._smoothing("gaussian"))
        smoothing_menu.add_command(label="Median Filter", command=lambda: self._smoothing("median"))
        enh_menu.add_cascade(label="Smoothing", menu=smoothing_menu)

        sharp_menu = tk.Menu(enh_menu, tearoff=0)
        sharp_menu.add_command(label="Highpass Filter", command=self._highpass)
        sharp_menu.add_command(label="Highboost Filter", command=self._highboost)
        enh_menu.add_cascade(label="Sharpening", menu=sharp_menu)

        freq_menu = tk.Menu(enh_menu, tearoff=0)
        freq_menu.add_command(label="ILPF", command=lambda: self._freq_filter("ilpf"))
        freq_menu.add_command(label="BLPF", command=lambda: self._freq_filter("blpf"))
        freq_menu.add_command(label="IHPF", command=lambda: self._freq_filter("ihpf"))
        freq_menu.add_command(label="BHPF", command=lambda: self._freq_filter("bhpf"))
        enh_menu.add_cascade(label="Frequency Domain", menu=freq_menu)

        menubar.add_cascade(label="Enhancement", menu=enh_menu)

        # NOISE
        noise_menu = tk.Menu(menubar, tearoff=0)
        noise_menu.add_command(label="Gaussian Noise", command=lambda: self._noise("gaussian"))
        noise_menu.add_command(label="Rayleigh Noise", command=lambda: self._noise("rayleigh"))
        noise_menu.add_command(label="Erlang Noise", command=lambda: self._noise("erlang"))
        noise_menu.add_command(label="Exponential Noise", command=lambda: self._noise("exponential"))
        noise_menu.add_command(label="Uniform Noise", command=lambda: self._noise("uniform"))
        noise_menu.add_command(label="Impulse Noise", command=lambda: self._noise("s&p"))
        menubar.add_cascade(label="Noise", menu=noise_menu)

        # ABOUT
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="Info Tim Developer",
                               command=lambda: messagebox.showinfo("About", "Tim Developer\nGithub: ...\nYoutube: ..."))
        menubar.add_cascade(label="About", menu=about_menu)

        self.config(menu=menubar)

        # Canvas & Status Bar
        self.canvas = tk.Canvas(self, bg="#222")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.status = tk.Label(self, text="No image loaded", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # FILE HANDLING
    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.png *.jpeg *.bmp *.tiff")])
        if path:
            self.image = Image.open(path).convert("RGB")
            self.image_path = path
            self.history.clear()
            self.future.clear()
            self._show()

    def save_image(self):
        if not self.image:
            return
        if not self.image_path:
            return self.save_as_image()
        self.image.save(self.image_path)

    def save_as_image(self):
        if not self.image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            self.image.save(path)
            self.image_path = path

    # UNDO / REDO
    def push_history(self):
        if self.image is not None:
            self.history.append(self.image.copy())
            self.future.clear()

    def undo(self):
        if not self.history:
            messagebox.showinfo("Undo", "Tidak ada aksi sebelumnya.")
            return
        self.future.append(self.image.copy())
        self.image = self.history.pop()
        self._show()

    def redo(self):
        if not self.future:
            messagebox.showinfo("Redo", "Tidak ada aksi redo.")
            return
        self.history.append(self.image.copy())
        self.image = self.future.pop()
        self._show()

    # HELPER
    def _ensure(self):
        if self.image is None:
            messagebox.showwarning("Warning", "No image loaded.")
            return False
        return True

    def _show(self):
        self.canvas.delete("all")
        self.tk_image = pil_to_tk(self.image)
        self.canvas.create_image(10, 10, anchor="nw", image=self.tk_image)
        self.status.config(text=f"Image size: {self.image.size}")

    # BASIC OPS
    def _invert(self):
        if not self._ensure(): return
        self.push_history()
        self.image = basic.invert(self.image)
        self._show()

    def _convert_color(self, mode):
        if not self._ensure(): return
        self.push_history()
        self.image = basic.convert_color(self.image, mode)
        self._show()

    def _thresholding(self):
        if not self._ensure(): return
        self.push_history()
        t = simpledialog.askinteger("Threshold", "Masukkan nilai threshold (0-255):", initialvalue=128)
        self.image = basic.threshold(self.image, t)
        self._show()

    def _convolution(self):
        if not self._ensure(): return
        self.push_history()
        k = simpledialog.askstring("Kernel", "Kernel 3x3, pisahkan spasi:\nContoh: 0 -1 0 -1 5 -1 0 -1 0")
        if not k: return
        k = [float(x) for x in k.split()]
        kernel = [k[:3], k[3:6], k[6:]]
        self.image = basic.convolution(self.image, kernel)
        self._show()

    def _fft(self):
        if not self._ensure(): return
        self.push_history()
        self.image = basic.fft_spectrum(self.image)
        self._show()

    # ENHANCEMENT
    def _brightness(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat("Brightness", "Masukkan faktor:", initialvalue=1.2)
        self.image = enh.brightness(self.image, f)
        self._show()

    def _contrast(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat("Contrast", "Masukkan faktor:", initialvalue=1.2)
        self.image = enh.contrast(self.image, f)
        self._show()

    def _histeq(self):
        if not self._ensure(): return
        self.push_history()
        self.image = enh.hist_eq(self.image)
        self._show()

    def _smoothing(self, typ):
        if not self._ensure(): return
        self.push_history()
        self.image = filt.smoothing(self.image, typ)
        self._show()

    def _highpass(self):
        if not self._ensure(): return
        self.push_history()
        self.image = enh.highpass(self.image)
        self._show()

    def _highboost(self):
        if not self._ensure(): return
        self.push_history()
        a = simpledialog.askfloat("Highboost", "Faktor (1-10):", initialvalue=2.0)
        self.image = enh.highboost(self.image, a)
        self._show()

    def _freq_filter(self, typ):
        if not self._ensure(): return
        self.push_history()
        d0 = simpledialog.askinteger("Cutoff", "Cutoff frequency:", initialvalue=30)
        self.image = filt.frequency_filter(self.image, typ, d0)
        self._show()

    # GEOMETRIC OPS
    def _rotate(self):
        if not self._ensure(): return
        self.push_history()
        ang = simpledialog.askfloat("Rotate", "Angle:", initialvalue=90)
        self.image = geom.rotate(self.image, ang)
        self._show()

    def _translate(self):
        if not self._ensure(): return
        self.push_history()
        dx = simpledialog.askinteger("Translate", "dx:", initialvalue=10)
        dy = simpledialog.askinteger("Translate", "dy:", initialvalue=10)
        self.image = geom.translate(self.image, dx, dy)
        self._show()

    def _zoom(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat("Zoom", "Faktor:", initialvalue=1.5)
        self.image = geom.zoom(self.image, f)
        self._show()

    def _flip(self):
        if not self._ensure(): return
        self.push_history()
        horiz = messagebox.askyesno("Flip", "Flip horizontal? (No → vertical)")
        self.image = geom.flip(self.image, horiz)
        self._show()

    def _crop(self):
        if not self._ensure(): return
        self.push_history()
        w, h = self.image.size
        l = simpledialog.askinteger("Left", "Left:", initialvalue=0)
        t = simpledialog.askinteger("Top", "Top:", initialvalue=0)
        r = simpledialog.askinteger("Right", "Right:", initialvalue=w)
        b = simpledialog.askinteger("Bottom", "Bottom:", initialvalue=h)
        self.image = geom.crop(self.image, (l, t, r, b))
        self._show()

    # ARITHMETIC / BOOLEAN
    def _ask_second(self):
        path = filedialog.askopenfilename()
        if not path: return None
        img = Image.open(path).convert("RGB")
        return img.resize(self.image.size)

    def _arithmetic(self, op):
        if not self._ensure(): return
        other = self._ask_second()
        if other is None: return
        self.push_history()
        self.image = arith.arithmetic(self.image, other, op)
        self._show()

    def _boolean(self, op):
        if not self._ensure(): return

        if op == "not":
            self.push_history()
            self.image = boolop.logic_not(self.image)
            self._show()
            return

        other = self._ask_second()
        if other is None: return
        self.push_history()
        self.image = boolop.logic_op(self.image, other, op)
        self._show()

    # NOISE
    def _noise(self, typ):
        if not self._ensure(): return
        self.push_history()

        params = {}
        if typ == "gaussian":
            params["sigma"] = simpledialog.askfloat("Gaussian Noise", "Sigma:", initialvalue=20.0)
        elif typ == "rayleigh":
            params["scale"] = simpledialog.askfloat("Rayleigh", "Scale:", initialvalue=10.0)
        elif typ == "erlang":
            params["k"] = simpledialog.askinteger("Erlang", "k:", initialvalue=3)
            params["lam"] = simpledialog.askfloat("Lambda", "λ:", initialvalue=0.5)
        elif typ == "exponential":
            params["lam"] = simpledialog.askfloat("Lambda", "λ:", initialvalue=0.5)
        elif typ == "uniform":
            params["low"] = -20
            params["high"] = 20
        elif typ == "s&p":
            params["amount"] = 0.05

        self.image = noise_mod.add_noise(self.image, typ, **params)
        self._show()

    # EDGE DETECTION
    def _sobel(self):
        if not self._ensure(): return
        self.push_history()
        self.image = edge.sobel(self.image)
        self._show()

    def _prewitt(self):
        if not self._ensure(): return
        self.push_history()
        self.image = edge.prewitt(self.image)
        self._show()

    def _roberts(self):
        if not self._ensure(): return
        self.push_history()
        self.image = edge.roberts(self.image)
        self._show()

    def _laplacian(self):
        if not self._ensure(): return
        self.push_history()
        self.image = edge.laplacian(self.image)
        self._show()

    def _log(self):
        if not self._ensure(): return
        self.push_history()
        self.image = edge.log(self.image)
        self._show()

    def _canny(self):
        if not self._ensure(): return
        self.push_history()
        low = simpledialog.askinteger("Canny", "Low threshold:", initialvalue=50)
        high = simpledialog.askinteger("Canny", "High threshold:", initialvalue=150)
        self.image = edge.canny(self.image, low, high)
        self._show()


# MAIN LOOP
if __name__ == "__main__":
    app = ImageApp()
    app.mainloop()
