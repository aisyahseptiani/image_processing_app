import os
import traceback
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk, ImageEnhance

# Try to import customtkinter; if unavailable, use a minimal wrapper using ttk/style (fallback).
USE_CTK = True
try:
    import customtkinter as ctk
except Exception:
    USE_CTK = False
    # create minimal compatibility wrapper so code can use ctk names used below
    class _CTkFallback:
        CTk = tk.Tk
        CTkFrame = tk.Frame
        CTkLabel = tk.Label
        CTkButton = tk.Button
    ctk = _CTkFallback()

# Path to sample image (if present in environment)
SAMPLE_IMAGE_PATH = "/mnt/data/a2f32ddc-053f-4218-8604-6fb1d8adca86.png"

# Try import operations modules (optional)
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
    print("Warning: some operation modules not available")
    traceback.print_exc()

# Theme colors (used if customtkinter available)
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

# Utility: safely create a PhotoImage sized to fit (max_w, max_h)
def make_tk_image(pil_img, max_w, max_h):
    if pil_img is None:
        return None
    img_copy = pil_img.copy()
    img_copy.thumbnail((max_w, max_h), Image.LANCZOS)
    return ImageTk.PhotoImage(img_copy)

class ImageApp(ctk.CTk if USE_CTK else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Processing App")
        self.geometry("1400x860")
        self.minsize(1100, 700)

        # Image state
        self.original = None  # PIL.Image
        self.image = None     # processed PIL.Image
        self.image_path = None

        # Tk refs to prevent GC
        self._tk_orig = None
        self._tk_proc = None

        # History for undo/redo
        self.history = []
        self.future = []

        # Sidebar submenu frames mapping
        self.submenus = {}
        self.menu_buttons = {}

        # Build UI
        self._build_ui()

        # Keyboard shortcuts
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-y>", lambda e: self.redo())
        self.bind_all("<Control-s>", lambda e: self.save_image())

        # If sample image present, preload
        if os.path.exists(SAMPLE_IMAGE_PATH):
            try:
                self.original = Image.open(SAMPLE_IMAGE_PATH).convert("RGB")
                self.image = self.original.copy()
                self.image_path = SAMPLE_IMAGE_PATH
                self._render_both()
            except Exception:
                pass

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=BURGUNDY) if USE_CTK else tk.Frame(self, bg=BURGUNDY)
        header.pack(side="top", fill="x")
        title = ctk.CTkLabel(header, text=" Image Processing App ", font=("Segoe UI", 16, 'bold'),
                             text_color=TEXT) if USE_CTK else tk.Label(header, text=" Image Processing App ",
                                                                       font=("Segoe UI", 16, 'bold'),
                                                                       bg=BURGUNDY, fg=TEXT)
        title.pack(side="left", padx=16, pady=10)

        # Right-side header buttons container
        header_btns = ctk.CTkFrame(header, fg_color=BURGUNDY) if USE_CTK else tk.Frame(header, bg=BURGUNDY)
        header_btns.pack(side="right", padx=12)

        # Undo / Redo / Save symbols (Unicode) — will show even without icons
        undo_sym = "⎌"   # alternative unicode for undo-like
        redo_sym = "⤴"  # redo
        save_sym = "💾"

        btn_opts = {"fg_color": BURGUNDY_LIGHT, "hover_color": "#7C3B4A"} if USE_CTK else {}
        # Buttons
        undo_btn = ctk.CTkButton(header_btns, text=f"{undo_sym} Undo", command=self.undo,
                                 width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{undo_sym} Undo",
                                                                                 command=self.undo, bg=BURGUNDY_LIGHT,
                                                                                 fg=TEXT)
        redo_btn = ctk.CTkButton(header_btns, text=f"{redo_sym} Redo", command=self.redo,
                                 width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{redo_sym} Redo",
                                                                                 command=self.redo, bg=BURGUNDY_LIGHT,
                                                                                 fg=TEXT)
        save_btn = ctk.CTkButton(header_btns, text=f"{save_sym} Save", command=self.save_image,
                                 width=90, **btn_opts) if USE_CTK else tk.Button(header_btns, text=f"{save_sym} Save",
                                                                                 command=self.save_image, bg=BURGUNDY_LIGHT,
                                                                                 fg=TEXT)

        undo_btn.pack(side="left", padx=6)
        redo_btn.pack(side="left", padx=6)
        save_btn.pack(side="left", padx=6)

        # Main content
        content = ctk.CTkFrame(self, fg_color=BG) if USE_CTK else tk.Frame(self, bg=BG)
        content.pack(side="top", fill="both", expand=True, padx=12, pady=12)

        # Sidebar (left)
        sidebar = ctk.CTkFrame(content, width=300, fg_color=BURGUNDY) if USE_CTK else tk.Frame(content, width=300, bg=BURGUNDY)
        sidebar.pack(side="left", fill="y", padx=(0,12))
        if USE_CTK:
            ctk.CTkLabel(sidebar, text="TOOLS", font=("Segoe UI", 16, 'bold'), text_color=TEXT).pack(pady=(18,8))
        else:
            tk.Label(sidebar, text="TOOLS", font=("Segoe UI", 16, 'bold'), bg=BURGUNDY, fg=TEXT).pack(pady=(18,8))

        # Helper to add a top-level button with dropdown-style submenu directly below it
        def add_menu(title):
            # create button
            btn = ctk.CTkButton(sidebar, text=title, fg_color=BURGUNDY_LIGHT, text_color=TEXT,
                                anchor="w", command=lambda t=title: self._toggle_submenu(t)) if USE_CTK else tk.Button(sidebar, text=title,
                                                                                                                      bg=BURGUNDY_LIGHT, fg=TEXT,
                                                                                                                      anchor="w", command=lambda t=title: self._toggle_submenu(t))
            btn.pack(fill="x", padx=12, pady=(8,2))
            # submenu frame placed immediately under button (pack but hidden)
            subframe = ctk.CTkFrame(sidebar, fg_color=BURGUNDY, height=10) if USE_CTK else tk.Frame(sidebar, bg=BURGUNDY, height=10)
            # We don't call pack() yet; will pack when shown so it appears under the button.
            self.submenus[title] = subframe
            self.menu_buttons[title] = btn
            return subframe

        # Build menus & submenu items (same structure as you had)
        file_sub = add_menu("File")
        # Use lambda wrappers so buttons call the functions
        def _pack_sub_button(parent, text, cmd):
            if USE_CTK:
                b = ctk.CTkButton(parent, text=text, command=cmd, fg_color=BURGUNDY_LIGHT)
            else:
                b = tk.Button(parent, text=text, command=cmd, bg=BURGUNDY_LIGHT, fg=TEXT)
            b.pack(fill="x", pady=6, padx=(8,8))
            return b

        _pack_sub_button(file_sub, "Open Image", self.open_image)
        _pack_sub_button(file_sub, "Save Processed", self.save_image)
        _pack_sub_button(file_sub, "Save As...", self.save_as_image)

        basic_sub = add_menu("Basic Ops")
        _pack_sub_button(basic_sub, "Negative / Invert", self._invert)
        _pack_sub_button(basic_sub, "Grayscale", lambda: self._convert_color('L'))
        _pack_sub_button(basic_sub, "Thresholding", self._thresholding)
        _pack_sub_button(basic_sub, "Convolution (3x3)", self._convolution)
        _pack_sub_button(basic_sub, "Fourier Transform", self._fft)

        ar_sub = add_menu("Arithmetic")
        _pack_sub_button(ar_sub, "Add", lambda: self._arithmetic('add'))
        _pack_sub_button(ar_sub, "Subtract", lambda: self._arithmetic('sub'))
        _pack_sub_button(ar_sub, "Multiply", lambda: self._arithmetic('mul'))
        _pack_sub_button(ar_sub, "Divide", lambda: self._arithmetic('div'))

        bool_sub = add_menu("Boolean")
        _pack_sub_button(bool_sub, "NOT", lambda: self._boolean('not'))
        _pack_sub_button(bool_sub, "AND", lambda: self._boolean('and'))
        _pack_sub_button(bool_sub, "OR", lambda: self._boolean('or'))
        _pack_sub_button(bool_sub, "XOR", lambda: self._boolean('xor'))

        enh_sub = add_menu("Enhancement")
        _pack_sub_button(enh_sub, "Brightness", self._brightness)
        _pack_sub_button(enh_sub, "Contrast", self._contrast)
        _pack_sub_button(enh_sub, "Histogram Equalization", self._histeq)
        _pack_sub_button(enh_sub, "Gaussian Blur", lambda: self._smoothing('gaussian'))
        _pack_sub_button(enh_sub, "Median Filter", lambda: self._smoothing('median'))
        _pack_sub_button(enh_sub, "Highpass Filter", self._highpass)
        _pack_sub_button(enh_sub, "Highboost Filter", self._highboost)
        _pack_sub_button(enh_sub, "Frequency Domain", self._freq_dialog)

        noise_sub = add_menu("Noise")
        _pack_sub_button(noise_sub, "Gaussian Noise", lambda: self._noise('gaussian'))
        _pack_sub_button(noise_sub, "Rayleigh Noise", lambda: self._noise('rayleigh'))
        _pack_sub_button(noise_sub, "Erlang Noise", lambda: self._noise('erlang'))
        _pack_sub_button(noise_sub, "Exponential Noise", lambda: self._noise('exponential'))
        _pack_sub_button(noise_sub, "Uniform Noise", lambda: self._noise('uniform'))
        _pack_sub_button(noise_sub, "Salt & Pepper", lambda: self._noise('s&p'))

        edge_sub = add_menu("Edge Detection")
        _pack_sub_button(edge_sub, "Sobel", self._sobel)
        _pack_sub_button(edge_sub, "Prewitt", self._prewitt)
        _pack_sub_button(edge_sub, "Roberts", self._roberts)
        _pack_sub_button(edge_sub, "Laplacian", self._laplacian)
        _pack_sub_button(edge_sub, "LoG", self._log)
        _pack_sub_button(edge_sub, "Canny", self._canny)

        geo_sub = add_menu("Geometrics")
        _pack_sub_button(geo_sub, "Translate", self._translate)
        _pack_sub_button(geo_sub, "Rotate", self._rotate)
        _pack_sub_button(geo_sub, "Zoom", self._zoom)
        _pack_sub_button(geo_sub, "Flip", self._flip)
        _pack_sub_button(geo_sub, "Crop", self._crop)

        about_sub = add_menu("About")
        _pack_sub_button(about_sub, "Dev Info", lambda: messagebox.showinfo("About", "Tim Developer\nGithub: mimey09"))

        # Preview panels (right)
        preview = ctk.CTkFrame(content, fg_color=BG) if USE_CTK else tk.Frame(content, bg=BG)
        preview.pack(side="right", fill="both", expand=True)

        titles = ctk.CTkFrame(preview, fg_color=BG) if USE_CTK else tk.Frame(preview, bg=BG)
        titles.pack(side="top", fill="x")
        left_label = ctk.CTkLabel(titles, text="Original Image", text_color=BURGUNDY, font=("Segoe UI", 14, 'bold')) if USE_CTK else tk.Label(titles, text="Original Image", fg=BURGUNDY, bg=BG, font=("Segoe UI", 14, 'bold'))
        right_label = ctk.CTkLabel(titles, text="Processed Image", text_color=BURGUNDY, font=("Segoe UI", 14, 'bold')) if USE_CTK else tk.Label(titles, text="Processed Image", fg=BURGUNDY, bg=BG, font=("Segoe UI", 14, 'bold'))
        left_label.pack(side="left", expand=True)
        right_label.pack(side="right", expand=True)

        canv_cont = ctk.CTkFrame(preview, fg_color=BG) if USE_CTK else tk.Frame(preview, bg=BG)
        canv_cont.pack(side="top", fill="both", expand=True, pady=6)

        left_card = ctk.CTkFrame(canv_cont, fg_color=PANEL, corner_radius=8) if USE_CTK else tk.Frame(canv_cont, bg=PANEL)
        left_card.pack(side="left", fill="both", expand=True, padx=(8,4), pady=8)
        right_card = ctk.CTkFrame(canv_cont, fg_color=PANEL, corner_radius=8) if USE_CTK else tk.Frame(canv_cont, bg=PANEL)
        right_card.pack(side="right", fill="both", expand=True, padx=(4,8), pady=8)

        # Use tk.Canvas for pixel rendering (works in both CTkFrame and Frame)
        self.canvas_original = tk.Canvas(left_card, bg="#0f0f0f", highlightthickness=0)
        self.canvas_original.pack(fill="both", expand=True, padx=12, pady=12)
        self.canvas_processed = tk.Canvas(right_card, bg="#0f0f0f", highlightthickness=0)
        self.canvas_processed.pack(fill="both", expand=True, padx=12, pady=12)

        # status bar
        self.status = ctk.CTkLabel(self, text="No image loaded", fg_color=BURGUNDY, text_color=TEXT) if USE_CTK else tk.Label(self, text="No image loaded", bg=BURGUNDY, fg=TEXT)
        self.status.pack(side="bottom", fill="x")

        # Bind configure for re-rendering centered images (debounced)
        self._resize_job = None
        self.canvas_original.bind("<Configure>", lambda e: self._on_canvas_configure())
        self.canvas_processed.bind("<Configure>", lambda e: self._on_canvas_configure())

    # Toggle submenu visibility: show below its button; collapse others
    def _toggle_submenu(self, name):
        for k, f in self.submenus.items():
            if k == name:
                # Toggle: if visible -> hide; else show
                if f.winfo_ismapped():
                    f.pack_forget()
                else:
                    # pack right after the button so it appears as dropdown
                    # to ensure order, we repack everything in sidebar in a consistent order:
                    parent = f.master
                    # remove all submenu frames temporarily so we can reinsert in order
                    # We'll simply pack the target submenu right after its corresponding button
                    # First collapse other submenus
                    for kk, ff in self.submenus.items():
                        if ff.winfo_ismapped():
                            ff.pack_forget()
                    # Now pack this submenu below its button
                    # To ensure it appears immediately under the menu button, use pack with padx to line up.
                    f.pack(fill="x", padx=18, after=self.menu_buttons[name])
            else:
                # collapse others
                if f.winfo_ismapped():
                    f.pack_forget()

    # -------------------------
    # File handling
    # -------------------------
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.bmp *.tiff")])
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
            messagebox.showinfo("Save", "No processed image to save.")
            return
        # If image_path exists, confirm overwrite
        if self.image_path and os.path.exists(self.image_path):
            confirm = messagebox.askyesno("Save", f"Overwrite existing file?\n{self.image_path}")
            if confirm:
                try:
                    self.image.save(self.image_path)
                    messagebox.showinfo("Save", f"Saved to {self.image_path}")
                    return
                except Exception:
                    traceback.print_exc()
                    messagebox.showerror("Save", "Failed to save to existing path; choose Save As.")
            # if not confirmed fallthrough to save as
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
            messagebox.showinfo("Undo", "No previous action.")
            return
        try:
            self.future.append(self.image.copy() if self.image else None)
            self.image = self.history.pop()
            self._render_both()
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Undo", "Undo failed.")

    def redo(self):
        if not self.future:
            messagebox.showinfo("Redo", "No redo available.")
            return
        try:
            self.history.append(self.image.copy() if self.image else None)
            nxt = self.future.pop()
            if nxt is not None:
                self.image = nxt
            self._render_both()
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Redo", "Redo failed.")

    # -------------------------
    # Rendering centered images
    # -------------------------
    def _on_canvas_configure(self):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._render_both)

    def _render_single(self, canvas, pil_img):
        canvas.delete("all")
        if pil_img is None:
            return
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 4 or h <= 4:
            return
        pad = 16
        max_w = max(1, w - pad)
        max_h = max(1, h - pad)
        tk_img = make_tk_image(pil_img, max_w, max_h)
        if tk_img is None:
            return
        canvas.create_image(w//2, h//2, image=tk_img, anchor="center")
        # store reference on canvas to prevent GC
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
    # Helper ensure
    # -------------------------
    def _ensure(self):
        if self.image is None:
            messagebox.showwarning("Warning", "No image loaded.")
            return False
        return True

    # -------------------------
    # BASIC OPS wrappers
    # -------------------------
    def _invert(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if basic and hasattr(basic, 'invert'):
                self.image = basic.invert(self.image)
            else:
                r, g, b = self.image.split()
                r = r.point(lambda i: 255 - i)
                g = g.point(lambda i: 255 - i)
                b = b.point(lambda i: 255 - i)
                self.image = Image.merge('RGB', (r, g, b))
        except Exception:
            traceback.print_exc()
            messagebox.showerror("Invert", "Failed to invert")
        self._render_both()

    def _convert_color(self, mode):
        if not self._ensure(): return
        self.push_history()
        try:
            if basic and hasattr(basic, 'convert_color'):
                self.image = basic.convert_color(self.image, mode)
            else:
                if mode == 'L':
                    self.image = self.image.convert('L').convert('RGB')
                elif mode == 'binary':
                    t = simpledialog.askinteger('Threshold','Enter threshold (0-255):', initialvalue=128)
                    if t is None: return
                    gray = self.image.convert('L')
                    bw = gray.point(lambda p: 255 if p > t else 0)
                    self.image = bw.convert('RGB')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Convert', 'Failed to convert color')
        self._render_both()

    def _thresholding(self):
        if not self._ensure(): return
        self.push_history()
        t = simpledialog.askinteger('Threshold','Masukkan nilai threshold (0-255):', initialvalue=128)
        if t is None: return
        try:
            if basic and hasattr(basic, 'threshold'):
                self.image = basic.threshold(self.image, t)
            else:
                import numpy as np
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
        k = simpledialog.askstring('Kernel','Kernel 3x3, pisahkan spasi:\nContoh: 0 -1 0 -1 5 -1 0 -1 0')
        if not k: return
        try:
            vals = [float(x) for x in k.split()]
            if len(vals) < 9:
                raise ValueError("Kernel must have 9 values")
            kernel = [vals[:3], vals[3:6], vals[6:9]]
            if basic and hasattr(basic, 'convolution'):
                self.image = basic.convolution(self.image, kernel)
            else:
                # fallback simple convolution using numpy (valid for grayscale per-channel)
                import numpy as np
                arr = np.array(self.image).astype('float32')
                h, w = arr.shape[:2]
                pad = 1
                # pad with zeros
                if arr.ndim == 3:
                    padded = np.pad(arr, ((pad,pad),(pad,pad),(0,0)), mode='edge')
                    out = np.zeros_like(arr)
                    karr = np.array(kernel)
                    for y in range(h):
                        for x in range(w):
                            for c in range(3):
                                region = padded[y:y+3, x:x+3, c]
                                out[y,x,c] = (region * karr).sum()
                else:
                    padded = np.pad(arr, ((pad,pad),(pad,pad)), mode='edge')
                    out = np.zeros_like(arr)
                    karr = np.array(kernel)
                    for y in range(h):
                        for x in range(w):
                            region = padded[y:y+3, x:x+3]
                            out[y,x] = (region * karr).sum()
                # normalize/clamp
                out = out.clip(0,255).astype('uint8')
                from PIL import Image
                self.image = Image.fromarray(out)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Convolution','Invalid kernel or convolution failed')
        self._render_both()

    def _fft(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if basic and hasattr(basic, 'fft_spectrum'):
                self.image = basic.fft_spectrum(self.image)
            elif filt and hasattr(filt, 'frequency_filter'):
                self.image = filt.frequency_filter(self.image, 'ilpf', 30)
            else:
                messagebox.showinfo('FFT','FFT not available')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('FFT','Failed')
        self._render_both()

    # -------------------------
    # ENHANCEMENT
    # -------------------------
    def _brightness(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat('Brightness','Masukkan faktor:', initialvalue=1.2)
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
        f = simpledialog.askfloat('Contrast','Masukkan faktor:', initialvalue=1.2)
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
                messagebox.showinfo('HistEq','Not available')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('HistEq','Failed')
        self._render_both()

    def _smoothing(self, typ):
        if not self._ensure(): return
        self.push_history()
        try:
            if filt and hasattr(filt, 'smoothing'):
                self.image = filt.smoothing(self.image, typ)
            else:
                messagebox.showinfo('Smoothing','Not available')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Smoothing','Failed')
        self._render_both()

    def _highpass(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if enh and hasattr(enh, 'highpass'):
                self.image = enh.highpass(self.image)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Highpass','Failed')
        self._render_both()

    def _highboost(self):
        if not self._ensure(): return
        self.push_history()
        a = simpledialog.askfloat('Highboost','Faktor (1-10):', initialvalue=2.0)
        if a is None: return
        try:
            if enh and hasattr(enh, 'highboost'):
                self.image = enh.highboost(self.image, a)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Highboost','Failed')
        self._render_both()

    def _freq_dialog(self):
        if not self._ensure(): return
        typ = simpledialog.askstring('Freq Filter','Type (ilpf/blpf/ihpf/bhpf):', initialvalue='ilpf')
        if not typ: return
        d0 = simpledialog.askinteger('Cutoff','Cutoff frequency:', initialvalue=30)
        if d0 is None: return
        self._freq_filter(typ, d0)

    def _freq_filter(self, typ, d0):
        if not self._ensure(): return
        self.push_history()
        try:
            if filt and hasattr(filt, 'frequency_filter'):
                self.image = filt.frequency_filter(self.image, typ, d0)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('FreqFilter','Failed')
        self._render_both()

    # -------------------------
    # GEOMETRICS
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
                w, h = self.image.size
                new_w = w + abs(dx)
                new_h = h + abs(dy)
                new_img = Image.new('RGB', (new_w, new_h), (0,0,0))
                ox = max(dx, 0)
                oy = max(dy, 0)
                new_img.paste(self.image, (ox, oy))
                self.image = new_img
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Translate','Failed')
        self._render_both()

    def _zoom(self):
        if not self._ensure(): return
        self.push_history()
        f = simpledialog.askfloat('Zoom','Faktor:', initialvalue=1.5)
        if f is None: return
        try:
            if geom and hasattr(geom, 'zoom'):
                self.image = geom.zoom(self.image, f)
            else:
                w, h = self.image.size
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
        w, h = self.image.size
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

    # -------------------------
    # ARITHMETIC / BOOLEAN
    # -------------------------
    def _ask_second(self):
        path = filedialog.askopenfilename(filetypes=[('Image Files','*.jpg *.png *.jpeg *.bmp *.tiff')])
        if not path: return None
        try:
            img = Image.open(path).convert('RGB')
        except Exception:
            messagebox.showerror('Open second','Failed to open second image')
            return None
        try:
            img = img.resize(self.image.size)
        except Exception:
            pass
        return img

    def _arithmetic(self, op):
        if not self._ensure(): return
        other = self._ask_second()
        if other is None: return
        self.push_history()
        try:
            if arith and hasattr(arith, 'arithmetic'):
                res = arith.arithmetic(self.image, other, op)
                if isinstance(res, tuple):
                    res = res[0]
                self.image = res
            else:
                import numpy as np
                a = np.array(self.image).astype('float32')
                b = np.array(other).astype('float32')
                if op == 'add': r = a + b
                elif op == 'sub': r = a - b
                elif op == 'mul': r = (a * b) / 255.0
                elif op == 'div':
                    b[b == 0] = 1
                    r = (a / b) * 255.0
                else: r = a
                r = r.clip(0,255).astype('uint8')
                from PIL import Image
                self.image = Image.fromarray(r)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Arithmetic','Failed')
        self._render_both()

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
                messagebox.showerror('Boolean NOT','Failed')
            self._render_both()
            return
        other = self._ask_second()
        if other is None: return
        self.push_history()
        try:
            if boolop and hasattr(boolop, 'logic_op'):
                self.image = boolop.logic_op(self.image, other, op)
            else:
                import numpy as np
                a = np.array(self.image.convert('L')) > 128
                b = np.array(other.convert('L')) > 128
                if op == 'and': r = a & b
                elif op == 'or': r = a | b
                elif op == 'xor': r = a ^ b
                else: r = a
                out = (r.astype('uint8') * 255)
                self.image = Image.fromarray(out).convert('RGB')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Boolean','Failed')
        self._render_both()

    # -------------------------
    # NOISE
    # -------------------------
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
        elif typ == 's&p':
            amt = simpledialog.askfloat('Amount','Amount (0-1):', initialvalue=0.05)
            if amt is None: return
            params['amount'] = amt
        try:
            if noise_mod and hasattr(noise_mod, 'add_noise'):
                self.image = noise_mod.add_noise(self.image, typ, **params)
            else:
                messagebox.showinfo('Noise','Noise module not available')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Noise','Failed')
        self._render_both()

    # -------------------------
    # EDGE DETECTION
    # -------------------------
    def _sobel(self):
        if not self._ensure(): return
        self.push_history()
        try:
            if edge and hasattr(edge, 'sobel'):
                self.image = edge.sobel(self.image)
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
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Canny','Failed')
        self._render_both()


# MAIN LOOP
if __name__ == '__main__':
    app = ImageApp()
    app.mainloop()
