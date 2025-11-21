import os
import traceback
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageOps
import numpy as np

# Try import customtkinter and fallback to basic wrapper if unavailable
USE_CTK = True
try:
    import customtkinter as ctk
except Exception:
    USE_CTK = False
    class _CTkFallback:
        CTk = tk.Tk
        CTkFrame = tk.Frame
        CTkLabel = tk.Label
        CTkButton = tk.Button
    ctk = _CTkFallback()

# Try import operations modules - optional (preserve fallbacks)
try:
    from operations import basic_ops as basic
    from operations import enhancement as enh
    from operations import filtering as filt
    from operations import geometrics as geom
    from operations import arithmetic as arith
    from operations import boolean as boolop
    from operations import noise as noise_mod
    from operations import edge_detection as edge
    from operations import utils
except Exception:
    basic = enh = filt = geom = arith = boolop = noise_mod = edge = utils = None
    # don't print traceback in GUI runtime, but helpful during development:
    # traceback.print_exc()

# Optional sample path (if you want to preload an image)
SAMPLE_IMAGE_PATH = "/mnt/data/a2f32ddc-053f-4218-8604-6fb1d8adca86.png"

# Colors (for CTk / fallback)
BURGUNDY = "#4A1F2D"
BURGUNDY_LIGHT = "#6A3244"
BG = "#121213"
PANEL = "#2b1b22"
CARD = "#171717"
TEXT = "#FFFFFF"

if USE_CTK:
    try:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
    except Exception:
        pass

# Utils
def make_tk_image(pil_img, max_w, max_h):
    if pil_img is None:
        return None
    img_copy = pil_img.copy()
    img_copy.thumbnail((max_w, max_h), Image.LANCZOS)
    return ImageTk.PhotoImage(img_copy)

# Color conversion helpers
def rgb_to_hsv_img(img: Image.Image):
    return img.convert('RGB').convert('HSV').convert('RGB')

def rgb_to_cmy_img(img: Image.Image):
    arr = np.array(img.convert('RGB')).astype(np.uint8)
    cmy = 255 - arr
    return Image.fromarray(cmy)

def rgb_to_yuv_img(img: Image.Image):
    arr = np.array(img.convert('RGB')).astype(np.float32)
    r = arr[...,0]; g = arr[...,1]; b = arr[...,2]
    y = 0.299*r + 0.587*g + 0.114*b
    u = -0.14713*r - 0.28886*g + 0.436*b + 128
    v = 0.615*r - 0.51499*g - 0.10001*b + 128
    out = np.stack((y,u,v), axis=-1).clip(0,255).astype('uint8')
    return Image.fromarray(out)

def rgb_to_yiq_img(img: Image.Image):
    arr = np.array(img.convert('RGB')).astype(np.float32)
    r = arr[...,0]; g = arr[...,1]; b = arr[...,2]
    y = 0.299*r + 0.587*g + 0.114*b
    i = 0.596*r - 0.274*g - 0.322*b
    q = 0.211*r - 0.523*g + 0.312*b
    out = np.stack((y, (i+128), (q+128)), axis=-1).clip(0,255).astype('uint8')
    return Image.fromarray(out)

def pseudo_color(img: Image.Image):
    gray = np.array(img.convert('L')).astype(np.float32)
    norm = (gray - gray.min()) / max(1e-8, (gray.max()-gray.min()))
    r = (255 * np.clip(4*(norm-0.75), 0, 1)).astype('uint8')
    g = (255 * np.clip(4*(norm-0.25) - np.clip(4*(norm-0.75),0,1), 0, 1)).astype('uint8')
    b = (255 * np.clip(4*(0.5 - norm), 0, 1)).astype('uint8')
    out = np.stack((r,g,b), axis=-1)
    return Image.fromarray(out)

class ImageApp(ctk.CTk if USE_CTK else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Processing App - 2025")
        self.geometry("1400x860")
        self.minsize(1100,700)

        # Image state
        self.original = None
        self.image = None
        self.image_path = None

        # History
        self.history = []
        self.future = []

        # UI maps
        self.submenus = {}
        self.menu_buttons = {}

        # build ui
        self._build_ui()

        # keybindings
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-y>", lambda e: self.redo())
        self.bind_all("<Control-s>", lambda e: self.save_image())

        # preload sample if exists
        if os.path.exists(SAMPLE_IMAGE_PATH):
            try:
                self.original = Image.open(SAMPLE_IMAGE_PATH).convert("RGB")
                self.image = self.original.copy()
                self.image_path = SAMPLE_IMAGE_PATH
                self._render_both()
            except Exception:
                pass

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BURGUNDY) if USE_CTK else tk.Frame(self, bg=BURGUNDY)
        header.pack(side="top", fill="x")
        title = ctk.CTkLabel(header, text=" Image Processing App ", font=("Segoe UI",16,'bold'), text_color=TEXT) if USE_CTK else tk.Label(header, text=" Image Processing App ", font=("Segoe UI",16,'bold'), bg=BURGUNDY, fg=TEXT)
        title.pack(side="left", padx=16, pady=10)

        header_btns = ctk.CTkFrame(header, fg_color=BURGUNDY) if USE_CTK else tk.Frame(header, bg=BURGUNDY)
        header_btns.pack(side="right", padx=12)

        undo_sym, redo_sym, save_sym = "⎌", "⤴", "💾"
        btn_opts = {"fg_color": BURGUNDY_LIGHT, "hover_color": "#7C3B4A"} if USE_CTK else {}

        undo_btn = ctk.CTkButton(header_btns, text=f"{undo_sym} Undo", command=self.undo, width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{undo_sym} Undo", command=self.undo, bg=BURGUNDY_LIGHT, fg=TEXT)
        redo_btn = ctk.CTkButton(header_btns, text=f"{redo_sym} Redo", command=self.redo, width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{redo_sym} Redo", command=self.redo, bg=BURGUNDY_LIGHT, fg=TEXT)
        save_btn = ctk.CTkButton(header_btns, text=f"{save_sym} Save", command=self.save_image, width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{save_sym} Save", command=self.save_image, bg=BURGUNDY_LIGHT, fg=TEXT)
        undo_btn.pack(side="left", padx=6); redo_btn.pack(side="left", padx=6); save_btn.pack(side="left", padx=6)

        content = ctk.CTkFrame(self, fg_color=BG) if USE_CTK else tk.Frame(self, bg=BG)
        content.pack(side="top", fill="both", expand=True, padx=12, pady=12)

        # Sidebar
        sidebar = ctk.CTkFrame(content, width=300, fg_color=BURGUNDY) if USE_CTK else tk.Frame(content, width=300, bg=BURGUNDY)
        sidebar.pack(side="left", fill="y", padx=(0,12))
        if USE_CTK:
            ctk.CTkLabel(sidebar, text="TOOLS", font=("Segoe UI",16,'bold'), text_color=TEXT).pack(pady=(18,8))
        else:
            tk.Label(sidebar, text="TOOLS", font=("Segoe UI",16,'bold'), bg=BURGUNDY, fg=TEXT).pack(pady=(18,8))

        def add_menu(title):
            btn = ctk.CTkButton(sidebar, text=title, fg_color=BURGUNDY_LIGHT, text_color=TEXT, anchor="w", command=lambda t=title: self._toggle_submenu(t)) if USE_CTK else tk.Button(sidebar, text=title, bg=BURGUNDY_LIGHT, fg=TEXT, anchor="w", command=lambda t=title: self._toggle_submenu(t))
            btn.pack(fill="x", padx=12, pady=(8,2))
            subframe = ctk.CTkFrame(sidebar, fg_color=BURGUNDY, height=10) if USE_CTK else tk.Frame(sidebar, bg=BURGUNDY, height=10)
            self.submenus[title] = subframe
            self.menu_buttons[title] = btn
            return subframe

        def _pack_btn(parent, text, cmd):
            if USE_CTK:
                b = ctk.CTkButton(parent, text=text, command=cmd, fg_color=BURGUNDY_LIGHT)
            else:
                b = tk.Button(parent, text=text, command=cmd, bg=BURGUNDY_LIGHT, fg=TEXT)
            b.pack(fill="x", pady=6, padx=(8,8))
            return b

        # FILE
        file_sub = add_menu("File")
        _pack_btn(file_sub, "Open Image", self.open_image)
        _pack_btn(file_sub, "Save Processed", self.save_image)
        _pack_btn(file_sub, "Save As...", self.save_as_image)

        # BASIC OPS
        basic_sub = add_menu("Basic Ops")
        _pack_btn(basic_sub, "Arithmetic", lambda: self._select_arithmetic())
        _pack_btn(basic_sub, "Boolean", lambda: self._boolean_dialog())
        _pack_btn(basic_sub, "Thresholding", self._thresholding)
        _pack_btn(basic_sub, "Convolution (3x3)", self._convolution)
        _pack_btn(basic_sub, "Fourier Transform", self._fft)
        _pack_btn(basic_sub, "Colouring", lambda: self._colouring_dialog())

        # ENHANCEMENT
        enh_sub = add_menu("Enhancement")
        _pack_btn(enh_sub, "Brightness", self._brightness)
        _pack_btn(enh_sub, "Contrast", self._contrast)
        _pack_btn(enh_sub, "Histogram Equalization", self._histeq)
        _pack_btn(enh_sub, "Smoothing (Spatial)", lambda: self._smoothing_dialog(spatial=True))
        _pack_btn(enh_sub, "Smoothing (Frequency)", lambda: self._smoothing_dialog(spatial=False))
        _pack_btn(enh_sub, "Sharpening (Spatial)", lambda: self._sharpening_dialog(spatial=True))
        _pack_btn(enh_sub, "Sharpening (Frequency)", lambda: self._sharpening_dialog(spatial=False))

        # NOISE
        noise_sub = add_menu("Noise")
        _pack_btn(noise_sub, "Gaussian Noise", lambda: self._noise('gaussian'))
        _pack_btn(noise_sub, "Rayleigh Noise", lambda: self._noise('rayleigh'))
        _pack_btn(noise_sub, "Erlang Noise", lambda: self._noise('erlang'))
        _pack_btn(noise_sub, "Exponential Noise", lambda: self._noise('exponential'))
        _pack_btn(noise_sub, "Uniform Noise", lambda: self._noise('uniform'))
        _pack_btn(noise_sub, "Impulse Noise", lambda: self._noise('impulse'))

        # EDGE
        edge_sub = add_menu("Edge Detection")
        _pack_btn(edge_sub, "Sobel", self._sobel)
        _pack_btn(edge_sub, "Prewitt", self._prewitt)
        _pack_btn(edge_sub, "Roberts", self._roberts)
        _pack_btn(edge_sub, "Laplacian", self._laplacian)
        _pack_btn(edge_sub, "LoG", self._log)
        _pack_btn(edge_sub, "Canny", self._canny)

        # GEOMETRICS
        geo_sub = add_menu("Geometrics")
        _pack_btn(geo_sub, "Translate", self._translate)
        _pack_btn(geo_sub, "Rotate", self._rotate)
        _pack_btn(geo_sub, "Zoom", self._zoom)
        _pack_btn(geo_sub, "Flip", self._flip)
        _pack_btn(geo_sub, "Crop", self._crop)

        about_sub = add_menu("About")
        _pack_btn(about_sub, "Dev Info", lambda: messagebox.showinfo("About","Tim Developer\nGithub: mimey09"))

        # Preview panels
        preview = ctk.CTkFrame(content, fg_color=BG) if USE_CTK else tk.Frame(content, bg=BG)
        preview.pack(side="right", fill="both", expand=True)

        titles = ctk.CTkFrame(preview, fg_color=BG) if USE_CTK else tk.Frame(preview, bg=BG)
        titles.pack(side="top", fill="x")
        (ctk.CTkLabel if USE_CTK else tk.Label)(titles, text="Original Image", text_color=BURGUNDY if USE_CTK else BURGUNDY, font=("Segoe UI",14,'bold')).pack(side="left", expand=True)
        (ctk.CTkLabel if USE_CTK else tk.Label)(titles, text="Processed Image", text_color=BURGUNDY if USE_CTK else BURGUNDY, font=("Segoe UI",14,'bold')).pack(side="right", expand=True)

        canv_cont = ctk.CTkFrame(preview, fg_color=BG) if USE_CTK else tk.Frame(preview, bg=BG)
        canv_cont.pack(side="top", fill="both", expand=True, pady=6)

        left_card = ctk.CTkFrame(canv_cont, fg_color=PANEL, corner_radius=8) if USE_CTK else tk.Frame(canv_cont, bg=PANEL)
        left_card.pack(side="left", fill="both", expand=True, padx=(8,4), pady=8)
        right_card = ctk.CTkFrame(canv_cont, fg_color=PANEL, corner_radius=8) if USE_CTK else tk.Frame(canv_cont, bg=PANEL)
        right_card.pack(side="right", fill="both", expand=True, padx=(4,8), pady=8)

        self.canvas_original = tk.Canvas(left_card, bg="#0f0f0f", highlightthickness=0)
        self.canvas_original.pack(fill="both", expand=True, padx=12, pady=12)
        self.canvas_processed = tk.Canvas(right_card, bg="#0f0f0f", highlightthickness=0)
        self.canvas_processed.pack(fill="both", expand=True, padx=12, pady=12)

        self.status = (ctk.CTkLabel(self, text="No image loaded", fg_color=BURGUNDY, text_color=TEXT) if USE_CTK else tk.Label(self, text="No image loaded", bg=BURGUNDY, fg=TEXT))
        self.status.pack(side="bottom", fill="x")

        # Bind canvas resize
        self._resize_job = None
        self.canvas_original.bind("<Configure>", lambda e: self._on_canvas_configure())
        self.canvas_processed.bind("<Configure>", lambda e: self._on_canvas_configure())

    # Toggle submenu
    def _toggle_submenu(self, name):
        for k, f in self.submenus.items():
            if k == name:
                if f.winfo_ismapped():
                    f.pack_forget()
                else:
                    for kk, ff in self.submenus.items():
                        if ff.winfo_ismapped():
                            ff.pack_forget()
                    parent = f.master
                    try:
                        f.pack(fill="x", padx=18, after=self.menu_buttons[name])
                    except Exception:
                        f.pack(fill="x", padx=18)
            else:
                if f.winfo_ismapped():
                    f.pack_forget()

    # -------------------------
    # File operations
    # -------------------------
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files","*.jpg *.png *.jpeg *.bmp *.tiff")])
        if path:
            try:
                self.original = Image.open(path).convert("RGB")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image:\n{e}")
                return
            self.image = self.original.copy()
            self.image_path = path
            self.history.clear()
            self.future.clear()
            self._render_both()

    def save_image(self):
        if self.image is None:
            messagebox.showinfo("Save","No processed image to save.")
            return
        if self.image_path and os.path.exists(self.image_path):
            confirm = messagebox.askyesno("Save", f"Overwrite existing file?\n{self.image_path}")
            if confirm:
                try:
                    self.image.save(self.image_path)
                    messagebox.showinfo("Save", f"Saved to {self.image_path}")
                    return
                except Exception:
                    traceback.print_exc()
                    messagebox.showerror("Save","Failed to save to existing path; using Save As.")
        self.save_as_image()

    def save_as_image(self):
        if self.image is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png"),("JPEG","*.jpg")])
        if not path:
            return
        try:
            self.image.save(path)
            self.image_path = path
            messagebox.showinfo("Save As", f"Saved to {path}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

    # -------------------------
    # History
    # -------------------------
    def push_history(self):
        if self.image is not None:
            self.history.append(self.image.copy())
            if len(self.history) > 50:
                self.history.pop(0)
            self.future.clear()

    def undo(self):
        if not self.history:
            messagebox.showinfo("Undo","No previous action.")
            return
        try:
            self.future.append(self.image.copy() if self.image else None)
            self.image = self.history.pop()
            self._render_both()
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Undo","Failed to undo.")

    def redo(self):
        if not self.future:
            messagebox.showinfo("Redo","No redo available.")
            return
        try:
            self.history.append(self.image.copy() if self.image else None)
            nxt = self.future.pop()
            if nxt is not None:
                self.image = nxt
            self._render_both()
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Redo","Failed to redo.")

    # -------------------------
    # Rendering
    # -------------------------
    def _on_canvas_configure(self):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._render_both)

    def _render_single(self, canvas, pil_img):
        canvas.delete("all")
        if pil_img is None:
            return
        w = canvas.winfo_width(); h = canvas.winfo_height()
        if w <= 4 or h <= 4:
            return
        pad = 16
        tk_img = make_tk_image(pil_img, max(1, w-pad), max(1, h-pad))
        if tk_img is None:
            return
        canvas.create_image(w//2, h//2, image=tk_img, anchor="center")
        canvas._img_ref = tk_img

    def _render_both(self):
        try:
            self._render_single(self.canvas_original, self.original)
            self._render_single(self.canvas_processed, self.image)
            if self.image:
                self.status.configure(text=f"Image size: {self.image.size[0]} x {self.image.size[1]}")
            elif self.original:
                self.status.configure(text=f"Original size: {self.original.size[0]} x {self.original.size[1]}")
            else:
                self.status.configure(text="No image loaded")
        except Exception:
            traceback.print_exc()
            self.status.configure(text="Render error")

    # -------------------------
    # Helpers
    # -------------------------
    def _ensure(self):
        if self.image is None:
            messagebox.showwarning("Warning","No image loaded.")
            return False
        return True

    def _ask_second(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files","*.jpg *.png *.jpeg *.bmp *.tiff")])
        if not path: return None
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            messagebox.showerror("Open second","Failed to open second image")
            return None
        try:
            img = img.resize(self.image.size)
        except Exception:
            pass
        return img

    # -------------------------
    # BASIC OPS implementations (and wrappers)
    # -------------------------
    def _select_arithmetic(self):
        if not self._ensure(): 
            return

        win = ctk.CTkToplevel(self)
        win.title("Arithmetic Operation")
        win.geometry("300x180")
        win.resizable(False, False)

        ctk.CTkLabel(win, text="Select Arithmetic Operation", font=("Segoe UI", 14, "bold")).pack(pady=10)

        options = ["add", "sub", "mul", "div"]
        selected = ctk.StringVar(value=options[0])

        dropdown = ctk.CTkOptionMenu(win, values=options, variable=selected)
        dropdown.pack(pady=10)

        def apply():
            op = selected.get()
            win.destroy()
            self._arithmetic(op)

        ctk.CTkButton(win, text="Apply", command=apply).pack(pady=10)


    def _arithmetic(self, op):
        if not self._ensure(): return
        other = self._ask_second()
        if other is None: return
        self.push_history()
        try:
            if arith and hasattr(arith, 'arithmetic'):
                res = arith.arithmetic(self.image, other, op)
                if isinstance(res, tuple): res = res[0]
                self.image = res
            else:
                a = np.array(self.image).astype('float32')
                b = np.array(other).astype('float32')
                if op == 'add':
                    r = a + b
                elif op == 'sub':
                    r = a - b
                elif op == 'mul':
                    r = (a * b) / 255.0
                elif op == 'div':
                    b[b == 0] = 1
                    r = (a / b) * 255.0
                else:
                    messagebox.showinfo("Arithmetic","Unknown operation")
                    return
                r = r.clip(0,255).astype('uint8')
                self.image = Image.fromarray(r)
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Arithmetic","Failed")
        self._render_both()

    def _boolean_dialog(self):
        if not self._ensure(): return
        dlg = tk.Toplevel(self)
        dlg.title("Boolean Operation")
        dlg.geometry("320x180")
        tk.Label(dlg, text="Operation:").pack(pady=(8,0))
        op_var = tk.StringVar(value="not")
        op_box = ttk.Combobox(dlg, textvariable=op_var, values=["not","and","or","xor"], state="readonly")
        op_box.pack(pady=6, padx=12, fill="x")

        def apply():
            op = op_var.get()
            dlg.destroy()
            self._boolean(op)

        tk.Button(dlg, text="Apply", command=apply).pack(pady=8)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).pack()

    def _boolean(self, op):
        if not self._ensure(): return
        if op == 'not':
            self.push_history()
            try:
                if boolop and hasattr(boolop, 'logic_not'):
                    self.image = boolop.logic_not(self.image)
                else:
                    r,g,b = self.image.split()
                    r = r.point(lambda i: 255-i)
                    g = g.point(lambda i: 255-i)
                    b = b.point(lambda i: 255-i)
                    self.image = Image.merge('RGB',(r,g,b))
            except Exception:
                traceback.print_exc()
                messagebox.showerror("Boolean NOT","Failed")
            self._render_both()
            return
        other = self._ask_second()
        if other is None: return
        self.push_history()
        try:
            if boolop and hasattr(boolop, 'logic_op'):
                self.image = boolop.logic_op(self.image, other, op)
            else:
                a = np.array(self.image.convert('L')) > 128
                b = np.array(other.convert('L')) > 128
                if op == 'and': r = a & b
                elif op == 'or': r = a | b
                elif op == 'xor': r = a ^ b
                else:
                    messagebox.showinfo("Boolean","Unknown boolean op")
                    return
                out = (r.astype('uint8') * 255)
                self.image = Image.fromarray(out).convert('RGB')
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Boolean","Failed")
        self._render_both()

    def _colouring_dialog(self):
        if not self._ensure(): return
        dlg = tk.Toplevel(self)
        dlg.title("Colouring")
        dlg.geometry("360x220")
        tk.Label(dlg, text="Colour mode:").pack(pady=(8,0))
        var = tk.StringVar(value="grayscale")
        box = ttk.Combobox(dlg, textvariable=var, values=["binary","grayscale","rgb","hsv","cmy","yuv","yiq","pseudo"], state="readonly")
        box.pack(pady=6, padx=12, fill="x")

        threshold_entry = None
        def on_mode_change(*_):
            nonlocal threshold_entry
            if threshold_entry:
                threshold_entry.pack_forget()
                threshold_entry = None
            if var.get() == 'binary':
                tk.Label(dlg, text="Threshold (0-255):").pack()
                threshold_entry = tk.Entry(dlg)
                threshold_entry.insert(0,"128")
                threshold_entry.pack()

        var.trace_add("write", on_mode_change)

        def apply():
            mode = var.get()
            t = None
            if mode == 'binary' and threshold_entry:
                try:
                    t = int(threshold_entry.get())
                except Exception:
                    messagebox.showinfo("Input","Invalid threshold")
                    return
            dlg.destroy()
            self._convert_color(mode, threshold=t)

        tk.Button(dlg, text="Apply", command=apply).pack(pady=8)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).pack()

    def _convert_color(self, mode, threshold=128):
        if not self._ensure(): return
        self.push_history()
        try:
            if mode == 'binary':
                t = threshold
                gray = self.image.convert('L')
                bw = gray.point(lambda p: 255 if p > t else 0)
                self.image = bw.convert('RGB')
            elif mode == 'grayscale':
                self.image = self.image.convert('L').convert('RGB')
            elif mode == 'rgb':
                self.image = self.image.convert('RGB')
            elif mode == 'hsv':
                self.image = rgb_to_hsv_img(self.image)
            elif mode == 'cmy':
                self.image = rgb_to_cmy_img(self.image)
            elif mode == 'yuv':
                self.image = rgb_to_yuv_img(self.image)
            elif mode == 'yiq':
                self.image = rgb_to_yiq_img(self.image)
            elif mode == 'pseudo':
                self.image = pseudo_color(self.image)
            else:
                messagebox.showinfo("Colouring","Unknown mode")
                return
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Colouring","Failed")
        self._render_both()

    def _thresholding(self):
        if not self._ensure(): return
        self.push_history()
        t = simpledialog.askinteger('Threshold','Enter threshold (0-255):', initialvalue=128)
        if t is None: return
        try:
            if basic and hasattr(basic, 'threshold'):
                self.image = basic.threshold(self.image, t)
            else:
                gray = self.image.convert('L')
                a = np.array(gray)
                a = ((a > t) * 255).astype('uint8')
                self.image = Image.fromarray(a).convert('RGB')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Threshold','Failed')
        self._render_both()

    def _convolution(self):
        if not self._ensure(): return
        self.push_history()
        # Dialog for kernel (but prefill common sharpen/blur options)
        dlg = tk.Toplevel(self)
        dlg.title("Convolution Kernel (3x3)")
        dlg.geometry("420x260")

        tk.Label(dlg, text="Select kernel preset or enter 9 values (space-separated):").pack(pady=(8,0))
        preset_var = tk.StringVar(value="Custom")
        preset_box = ttk.Combobox(dlg, textvariable=preset_var, values=["Custom","Identity","Sharpen","Edge","Box Blur"], state="readonly")
        preset_box.pack(pady=6, padx=12, fill="x")

        vals_entry = tk.Text(dlg, height=4)
        vals_entry.pack(padx=12, pady=6, fill="both", expand=True)
        vals_entry.insert("1.0", "0 -1 0 -1 5 -1 0 -1 0")

        def on_preset(*_):
            p = preset_var.get()
            if p == "Identity":
                vals_entry.delete("1.0","end"); vals_entry.insert("1.0","0 0 0 0 1 0 0 0 0")
            elif p == "Sharpen":
                vals_entry.delete("1.0","end"); vals_entry.insert("1.0","0 -1 0 -1 5 -1 0 -1 0")
            elif p == "Edge":
                vals_entry.delete("1.0","end"); vals_entry.insert("1.0","-1 -1 -1 -1 8 -1 -1 -1 -1")
            elif p == "Box Blur":
                vals_entry.delete("1.0","end"); vals_entry.insert("1.0","1 1 1 1 1 1 1 1 1")

        preset_box.bind("<<ComboboxSelected>>", on_preset)

        def apply():
            k = vals_entry.get("1.0","end").strip()
            dlg.destroy()
            try:
                vals = [float(x) for x in k.split()]
                if len(vals) < 9:
                    raise ValueError("Need 9 values")
                kernel = [vals[:3], vals[3:6], vals[6:9]]
                if basic and hasattr(basic, 'convolution'):
                    self.push_history()
                    self.image = basic.convolution(self.image, kernel)
                    self._render_both()
                else:
                    # fallback convolution
                    self.push_history()
                    arr = np.array(self.image).astype('float32')
                    h, w = arr.shape[:2]
                    pad = 1
                    karr = np.array(kernel)
                    if arr.ndim == 3:
                        padded = np.pad(arr, ((pad,pad),(pad,pad),(0,0)), mode='edge')
                        out = np.zeros_like(arr)
                        for y in range(h):
                            for x in range(w):
                                for c in range(3):
                                    region = padded[y:y+3, x:x+3, c]
                                    out[y,x,c] = (region * karr).sum()
                    else:
                        padded = np.pad(arr, ((pad,pad),(pad,pad)), mode='edge')
                        out = np.zeros_like(arr)
                        for y in range(h):
                            for x in range(w):
                                region = padded[y:y+3, x:x+3]
                                out[y,x] = (region * karr).sum()
                    out = out.clip(0,255).astype('uint8')
                    self.image = Image.fromarray(out)
                    self._render_both()
            except Exception:
                traceback.print_exc()
                messagebox.showerror('Convolution','Failed or invalid kernel')

        tk.Button(dlg, text="Apply", command=apply).pack(pady=6)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).pack()

    def _fft(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if basic and hasattr(basic, 'fft_spectrum'):
                self.image = basic.fft_spectrum(self.image)
            elif filt and hasattr(filt, 'frequency_filter'):
                self.image = filt.frequency_filter(self.image, 'ilpf', 30)
            else:
                messagebox.showinfo('FFT','FFT / frequency filtering not available (module missing).')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('FFT','Failed')
        self._render_both()

    # -------------------------
    # ENHANCEMENT implementations
    # -------------------------
    def _brightness(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat('Brightness','Factor (e.g. 1.2):', initialvalue=1.2)
        if f is None: return
        try:
            if enh and hasattr(enh, 'brightness'):
                self.image = enh.brightness(self.image, f)
            else:
                self.image = ImageEnhance.Brightness(self.image).enhance(f)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Brightness','Failed')
        self._render_both()

    def _contrast(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat('Contrast','Factor (e.g. 1.2):', initialvalue=1.2)
        if f is None: return
        try:
            if enh and hasattr(enh, 'contrast'):
                self.image = enh.contrast(self.image, f)
            else:
                self.image = ImageEnhance.Contrast(self.image).enhance(f)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Contrast','Failed')
        self._render_both()

    def _histeq(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if enh and hasattr(enh, 'hist_eq'):
                self.image = enh.hist_eq(self.image)
            elif enh and hasattr(enh, 'hist_equalization'):
                self.image = enh.hist_equalization(self.image)
            else:
                y = np.array(self.image.convert('L'))
                hist, bins = np.histogram(y.flatten(), 256, [0,256])
                cdf = hist.cumsum()
                cdf_m = np.ma.masked_equal(cdf,0)
                cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
                cdf = np.ma.filled(cdf_m,0).astype('uint8')
                y2 = cdf[y]
                self.image = Image.fromarray(y2).convert('RGB')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('HistEq','Failed')
        self._render_both()

    # Smoothing dialog using dropdown + parameter fields
    def _smoothing_dialog(self, spatial=True):
        if not self._ensure(): return
        dlg = tk.Toplevel(self)
        dlg.title("Smoothing")
        dlg.geometry("360x200")
        tk.Label(dlg, text="Choose smoothing type:").pack(pady=(8,0))
        if spatial:
            options = ["Lowpass (Box Blur)", "Median (3x3)"]
        else:
            options = ["ILPF (Ideal Lowpass)", "BLPF (Butterworth Lowpass)"]
        var = tk.StringVar(value=options[0])
        box = ttk.Combobox(dlg, textvariable=var, values=options, state="readonly")
        box.pack(pady=8, padx=12, fill="x")

        param_frame = tk.Frame(dlg)
        param_frame.pack(fill="x", padx=12)
        tk.Label(param_frame, text="Parameter (radius/cutoff/order):").pack(anchor="w")
        entry = tk.Entry(param_frame)
        entry.insert(0,"2" if spatial else "30")
        entry.pack(fill="x", pady=6)

        def apply():
            choice = var.get()
            val = entry.get().strip()
            dlg.destroy()
            try:
                if spatial:
                    if choice.startswith("Lowpass"):
                        r = float(val) if val else 2.0
                        self.push_history()
                        self.image = self.image.filter(ImageFilter.BoxBlur(r))
                    else:
                        self.push_history()
                        self.image = self.image.filter(ImageFilter.MedianFilter(size=3))
                else:
                    d0 = int(val) if val else 30
                    self.push_history()
                    if filt and hasattr(filt, 'frequency_filter'):
                        typ = 'ilpf' if choice.startswith("ILPF") else 'blpf'
                        self.image = filt.frequency_filter(self.image, typ, d0)
                    else:
                        messagebox.showinfo('Frequency Smoothing','Module for frequency filtering not available.')
                self._render_both()
            except Exception:
                traceback.print_exc()
                messagebox.showerror('Smoothing','Failed')

        tk.Button(dlg, text="Apply", command=apply).pack(pady=8)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).pack()

    # Sharpening dialog
    def _sharpening_dialog(self, spatial=True):
        if not self._ensure(): return
        dlg = tk.Toplevel(self)
        dlg.title("Sharpening")
        dlg.geometry("360x200")
        tk.Label(dlg, text="Choose sharpening type:").pack(pady=(8,0))
        if spatial:
            options = ["Highpass (3x3)", "Highboost (factor)"]
        else:
            options = ["IHPF (Ideal Highpass)", "BHPF (Butterworth Highpass)"]
        var = tk.StringVar(value=options[0])
        box = ttk.Combobox(dlg, textvariable=var, values=options, state="readonly")
        box.pack(pady=8, padx=12, fill="x")

        param_frame = tk.Frame(dlg)
        param_frame.pack(fill="x", padx=12)
        tk.Label(param_frame, text="Parameter (factor/cutoff/order):").pack(anchor="w")
        entry = tk.Entry(param_frame)
        entry.insert(0,"1.5" if spatial else "30")
        entry.pack(fill="x", pady=6)

        def apply():
            choice = var.get()
            val = entry.get().strip()
            dlg.destroy()
            try:
                if spatial:
                    if choice.startswith("Highpass"):
                        self.push_history()
                        kernel = ImageFilter.Kernel((3,3), [-1,-1,-1,-1,8,-1,-1,-1,-1], scale=None, offset=0)
                        self.image = self.image.filter(kernel)
                    else:
                        a = float(val) if val else 1.5
                        self.push_history()
                        blurred = self.image.filter(ImageFilter.GaussianBlur(radius=1))
                        orig = np.array(self.image).astype('float32')
                        b = np.array(blurred).astype('float32')
                        highboost = (orig + a*(orig - b)).clip(0,255).astype('uint8')
                        self.image = Image.fromarray(highboost)
                else:
                    d0 = int(val) if val else 30
                    self.push_history()
                    if filt and hasattr(filt, 'frequency_sharpen'):
                        typ = 'ihpf' if choice.startswith("IHPF") else 'bhpf'
                        self.image = filt.frequency_sharpen(self.image, typ, d0)
                    elif filt and hasattr(filt, 'frequency_filter'):
                        messagebox.showinfo('Freq Sharpen','Attempting frequency filter fallback')
                        typ = 'ihpf' if choice.startswith("IHPF") else 'bhpf'
                        self.image = filt.frequency_filter(self.image, typ, d0)
                    else:
                        messagebox.showinfo('Freq Sharpen','Frequency sharpening not available (module missing).')
                self._render_both()
            except Exception:
                traceback.print_exc()
                messagebox.showerror('Sharpening','Failed')

        tk.Button(dlg, text="Apply", command=apply).pack(pady=8)
        tk.Button(dlg, text="Cancel", command=dlg.destroy).pack()

    # Noise
    def _noise(self, typ):
        if not self._ensure(): return
        self.push_history()
        params = {}
        if typ == 'gaussian':
            s = simpledialog.askfloat('Gaussian Noise','Sigma:', initialvalue=20.0)
            if s is None: return
            params['sigma'] = s
        elif typ == 'rayleigh':
            sc = simpledialog.askfloat('Rayleigh','Scale:', initialvalue=10.0)
            if sc is None: return
            params['scale'] = sc
        elif typ == 'erlang':
            k = simpledialog.askinteger('Erlang','k:', initialvalue=3)
            lam = simpledialog.askfloat('Lambda','\u03bb:', initialvalue=0.5)
            if k is None or lam is None: return
            params['k'] = k; params['lam'] = lam
        elif typ == 'exponential':
            lam = simpledialog.askfloat('Lambda','\u03bb:', initialvalue=0.5)
            if lam is None: return
            params['lam'] = lam
        elif typ == 'uniform':
            params['low'] = -20; params['high'] = 20
        elif typ == 'impulse':
            amt = simpledialog.askfloat('Impulse Noise','Amount (0-1):', initialvalue=0.05)
            if amt is None: return
            params['amount'] = amt
        try:
            if noise_mod and hasattr(noise_mod, 'add_noise'):
                self.image = noise_mod.add_noise(self.image, typ, **params)
            else:
                arr = np.array(self.image).astype('int32')
                h,w = arr.shape[:2]
                if typ == 'impulse':
                    amount = params.get('amount', 0.05)
                    num = int(amount * h * w)
                    for _ in range(num):
                        y = np.random.randint(0,h); x = np.random.randint(0,w)
                        if np.random.rand() < 0.5:
                            arr[y,x] = [0,0,0]
                        else:
                            arr[y,x] = [255,255,255]
                    self.image = Image.fromarray(arr.astype('uint8'))
                elif typ == 'gaussian':
                    sigma = params.get('sigma', 20.0)
                    noise = np.random.normal(0, sigma, arr.shape).astype('int32')
                    out = (arr + noise).clip(0,255).astype('uint8')
                    self.image = Image.fromarray(out)
                else:
                    messagebox.showinfo('Noise','Noise type not implemented in fallback')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Noise','Failed')
        self._render_both()

    # -------------------------
    # EDGE wrappers (kept)
    # -------------------------
    def _sobel(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'sobel'):
                self.image = edge.sobel(self.image)
            else:
                messagebox.showinfo('Sobel','Edge module not available (use operations/edge_detection to add).')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Sobel','Failed')
        self._render_both()

    def _prewitt(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'prewitt'):
                self.image = edge.prewitt(self.image)
            else:
                messagebox.showinfo('Prewitt','Edge module not available.')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Prewitt','Failed')
        self._render_both()

    def _roberts(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'roberts'):
                self.image = edge.roberts(self.image)
            else:
                messagebox.showinfo('Roberts','Edge module not available.')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Roberts','Failed')
        self._render_both()

    def _laplacian(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'laplacian'):
                self.image = edge.laplacian(self.image)
            else:
                messagebox.showinfo('Laplacian','Edge module not available.')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Laplacian','Failed')
        self._render_both()

    def _log(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'log'):
                self.image = edge.log(self.image)
            else:
                messagebox.showinfo('LoG','Edge module not available.')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('LoG','Failed')
        self._render_both()

    def _canny(self):
        if not self._ensure(): return
        self.push_history()
        low = simpledialog.askinteger('Canny','Low threshold:', initialvalue=50)
        high = simpledialog.askinteger('Canny','High threshold:', initialvalue=150)
        if low is None or high is None: return
        try:
            if edge and hasattr(edge, 'canny'):
                self.image = edge.canny(self.image, low, high)
            else:
                messagebox.showinfo('Canny','Edge module not available.')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Canny','Failed')
        self._render_both()

    # -------------------------
    # GEOMETRICS (kept)
    # -------------------------
    def _rotate(self, ang=None):
        if not self._ensure(): return
        self.push_history()
        if ang is None:
            ang = simpledialog.askfloat('Rotate','Angle:', initialvalue=90)
            if ang is None: return
        try:
            if geom and hasattr(geom, 'rotate'):
                self.image = geom.rotate(self.image, ang)
            else:
                self.image = self.image.rotate(ang, expand=True)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Rotate','Failed')
        self._render_both()

    def _translate(self):
        if not self._ensure(): return
        self.push_history()
        dx = simpledialog.askinteger('Translate','dx:', initialvalue=10)
        dy = simpledialog.askinteger('Translate','dy:', initialvalue=10)
        if dx is None or dy is None: return
        try:
            if geom and hasattr(geom, 'translate'):
                self.image = geom.translate(self.image, dx, dy)
            else:
                w,h = self.image.size
                new_w = w + abs(dx); new_h = h + abs(dy)
                new_img = Image.new('RGB',(new_w,new_h),(0,0,0))
                ox = max(dx,0); oy = max(dy,0)
                new_img.paste(self.image,(ox,oy))
                self.image = new_img
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Translate','Failed')
        self._render_both()

    def _zoom(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat('Zoom','Factor:', initialvalue=1.5)
        if f is None: return
        try:
            if geom and hasattr(geom, 'zoom'):
                self.image = geom.zoom(self.image, f)
            else:
                w,h = self.image.size
                self.image = self.image.resize((int(w*f), int(h*f)), Image.LANCZOS)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Zoom','Failed')
        self._render_both()

    def _flip(self):
        if not self._ensure(): return
        self.push_history()
        horiz = messagebox.askyesno('Flip','Flip horizontal? (No -> vertical)')
        try:
            if geom and hasattr(geom, 'flip'):
                self.image = geom.flip(self.image, horiz)
            else:
                if horiz:
                    self.image = self.image.transpose(Image.FLIP_LEFT_RIGHT)
                else:
                    self.image = self.image.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Flip','Failed')
        self._render_both()

    def _crop(self):
        if not self._ensure(): return
        self.push_history()
        w,h = self.image.size
        l = simpledialog.askinteger('Left','Left:', initialvalue=0)
        t = simpledialog.askinteger('Top','Top:', initialvalue=0)
        r = simpledialog.askinteger('Right','Right:', initialvalue=w)
        b = simpledialog.askinteger('Bottom','Bottom:', initialvalue=h)
        if None in (l,t,r,b): return
        try:
            if geom and hasattr(geom, 'crop'):
                self.image = geom.crop(self.image, (l,t,r,b))
            else:
                self.image = self.image.crop((l,t,r,b))
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Crop','Failed')
        self._render_both()

# MAIN
if __name__ == '__main__':
    app = ImageApp()
    app.mainloop()
