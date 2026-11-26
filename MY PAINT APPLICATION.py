import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
from pathlib import Path

# Soft peach interface palette
PEACH_BG = "#FFE8D6"
PEACH_PANEL = "#FFD7BA"
PEACH_BUTTON = "#FFBE98"
PEACH_HOVER = "#FFA877"
TEXT_COLOR = "#5C3D2E"
FONT_MAIN = ("Arial", 10, "bold")

CANVAS_WIDTH = 900
CANVAS_HEIGHT = 550
MAX_UNDO = 30

root = tk.Tk()
root.title("MY PAINT APPLICATION")
root.geometry("1120x760")
root.minsize(1050, 700)
root.configure(bg=PEACH_BG)

# Drawing data is kept in a Pillow image so the saved file matches the canvas.
image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
draw = ImageDraw.Draw(image)
canvas_image = None
undo_stack = []

current_color = "#000000"
brush_size = 5
tool = "brush"
start_x = start_y = None
last_x = last_y = None
preview_shape = None
shape_filled = False

def save_undo():
    """Save the current image before a completed drawing action."""
    undo_stack.append(image.copy())
    if len(undo_stack) > MAX_UNDO:
        del undo_stack[0]
    update_undo_button()

def update_undo_button():
    undo_button.config(state="normal" if undo_stack else "disabled")

def undo():
    global image, draw, preview_shape
    if not undo_stack:
        return
    image = undo_stack.pop()
    draw = ImageDraw.Draw(image)
    preview_shape = None
    refresh_canvas()
    update_undo_button()

def refresh_canvas():
    global canvas_image
    canvas.delete("all")
    canvas_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor="nw", image=canvas_image)

def choose_color():
    global current_color, tool
    chosen = colorchooser.askcolor(color=current_color, title="Choose a drawing color")
    if chosen[1]:
        set_color(chosen[1])

def set_color(color):
    global current_color, tool
    current_color = color
    tool = "brush"
    color_button.config(bg=current_color, activebackground=current_color)
    status_label.config(text=f"Selected color: {current_color}")

def set_tool(selected_tool):
    global tool
    tool = selected_tool
    status_label.config(text=f"Tool: {selected_tool.title()}")

def change_brush_size(value):
    global brush_size
    brush_size = max(1, min(100, int(float(value))))
    size_value.config(text=str(brush_size))

def toggle_fill():
    global shape_filled
    shape_filled = bool(fill_var.get())
    status_label.config(text="Shapes: Filled" if shape_filled else "Shapes: Outline")

def start_drawing(event):
    global last_x, last_y, start_x, start_y, preview_shape
    last_x = start_x = event.x
    last_y = start_y = event.y
    preview_shape = None
    if tool in ("brush", "eraser"):
        save_undo()

def draw_motion(event):
    global last_x, last_y
    if tool in ("brush", "eraser"):
        color = "white" if tool == "eraser" else current_color
        draw.line((last_x, last_y, event.x, event.y),
                  fill=color, width=brush_size)
        # Round brush ends for a smoother stroke.
        radius = brush_size // 2
        draw.ellipse((event.x-radius, event.y-radius,
                     event.x+radius, event.y+radius), fill=color)
        last_x, last_y = event.x, event.y
        refresh_canvas()
    else:
        preview_shape_drawing(event)

def preview_shape_drawing(event):
    global preview_shape
    if preview_shape is not None:
        canvas.delete(preview_shape)
    fill_color = current_color if shape_filled else ""
    if tool == "line":
        preview_shape = canvas.create_line(
            start_x, start_y, event.x, event.y,
            fill=current_color, width=brush_size)
    elif tool == "rectangle":
        preview_shape = canvas.create_rectangle(
            start_x, start_y, event.x, event.y,
            outline=current_color, width=brush_size, fill=fill_color)
    elif tool == "oval":
        preview_shape = canvas.create_oval(
            start_x, start_y, event.x, event.y,
            outline=current_color, width=brush_size, fill=fill_color)
    elif tool == "triangle":
        points = (start_x, event.y, (start_x+event.x)//2, start_y,
                  event.x, event.y)
        preview_shape = canvas.create_polygon(
            points, outline=current_color, width=brush_size,
            fill=fill_color)

def finish_drawing(event):
    global preview_shape
    if tool not in ("brush", "eraser"):
        save_undo()
        fill_color = current_color if shape_filled else None
        if tool == "line":
            draw.line((start_x, start_y, event.x, event.y),
                      fill=current_color, width=brush_size)
        elif tool == "rectangle":
            draw.rectangle((start_x, start_y, event.x, event.y),
                          outline=current_color, fill=fill_color,
                          width=brush_size)
        elif tool == "oval":
            draw.ellipse((start_x, start_y, event.x, event.y),
                        outline=current_color, fill=fill_color,
                        width=brush_size)
        elif tool == "triangle":
            points = (start_x, event.y, (start_x+event.x)//2, start_y,
                      event.x, event.y)
            draw.polygon(points, outline=current_color, fill=fill_color)
            if not shape_filled:
                # Ensure outline thickness is consistent with the brush.
                draw.line(points + (points[0], points[1]),
                          fill=current_color, width=brush_size)
        preview_shape = None
        refresh_canvas()

def clear_canvas():
    global image, draw, preview_shape
    if not messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the canvas?"):
        return
    save_undo()
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    preview_shape = None
    refresh_canvas()
    status_label.config(text="Canvas cleared. Use Undo to restore your drawing.")

def open_image():
    global image, draw
    path = filedialog.askopenfilename(
        title="Open an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                   ("All files", ".")])
    if not path:
        return
    try:
        opened = Image.open(path).convert("RGB")
        # Fit the image to the drawing surface so its dimensions match exactly.
        opened = opened.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        save_undo()
        image = opened
        draw = ImageDraw.Draw(image)
        refresh_canvas()
        status_label.config(text=f"Opened: {Path(path).name}")
    except Exception as error:
        messagebox.showerror("Open Error", f"Could not open image:\n{error}")

def save_image():
    path = filedialog.asksaveasfilename(
        title="Save your drawing",
        defaultextension=".png",
        filetypes=[("PNG Image", ".png"), ("JPEG Image", ".jpg"),
                   ("Bitmap Image", "*.bmp")])
    if not path:
        return
    try:
        # Save the same Pillow image used to display the canvas.
        image.save(path)
        messagebox.showinfo("Saved", f"Your drawing was saved to:\n{path}")
        status_label.config(text=f"Saved: {Path(path).name}")
    except Exception as error:
        messagebox.showerror("Save Error", f"Could not save image:\n{error}")

def make_button(parent, label, command, **kwargs):
    return tk.Button(parent, text=label, command=command,
        bg=kwargs.get("bg", PEACH_BUTTON), fg=TEXT_COLOR,
        activebackground=PEACH_HOVER, activeforeground=TEXT_COLOR,
        font=FONT_MAIN, relief="flat", padx=9, pady=5,
        cursor="hand2", bd=0)

# Toolbar row one: tools
toolbar = tk.Frame(root, bg=PEACH_PANEL, padx=10, pady=8)
toolbar.pack(fill="x", padx=18, pady=(12, 6))

color_button = make_button(toolbar, "Choose Color", choose_color, bg=current_color)
color_button.pack(side="left", padx=3)
make_button(toolbar, "Brush", lambda: set_tool("brush")).pack(side="left", padx=3)
make_button(toolbar, "Eraser", lambda: set_tool("eraser")).pack(side="left", padx=3)
make_button(toolbar, "Line", lambda: set_tool("line")).pack(side="left", padx=3)
make_button(toolbar, "Rectangle", lambda: set_tool("rectangle")).pack(side="left", padx=3)
make_button(toolbar, "Oval", lambda: set_tool("oval")).pack(side="left", padx=3)
make_button(toolbar, "Triangle", lambda: set_tool("triangle")).pack(side="left", padx=3)

fill_var = tk.BooleanVar(value=False)
tk.Checkbutton(toolbar, text="Fill shapes", variable=fill_var,
    command=toggle_fill, bg=PEACH_PANEL, fg=TEXT_COLOR,
    activebackground=PEACH_PANEL, font=FONT_MAIN).pack(side="left", padx=8)

tk.Label(toolbar, text="Brush Size:", bg=PEACH_PANEL,
         fg=TEXT_COLOR, font=FONT_MAIN).pack(side="left", padx=(8, 3))
size_slider = tk.Scale(toolbar, from_=1, to=100, orient="horizontal",
    command=change_brush_size, length=150, bg=PEACH_PANEL,
    fg=TEXT_COLOR, troughcolor=PEACH_BUTTON, highlightthickness=0)
size_slider.set(5)
size_slider.pack(side="left", padx=2)
size_value = tk.Label(toolbar, text="5", bg=PEACH_PANEL,
                      fg=TEXT_COLOR, font=FONT_MAIN, width=3)
size_value.pack(side="left")

# Toolbar row two: six instant color buttons and file controls
toolbar2 = tk.Frame(root, bg=PEACH_PANEL, padx=10, pady=7)
toolbar2.pack(fill="x", padx=18, pady=4)
tk.Label(toolbar2, text="Quick Colors:", bg=PEACH_PANEL,
         fg=TEXT_COLOR, font=FONT_MAIN).pack(side="left", padx=(3, 7))
quick_colors = [
    ("Black", "#000000"), ("Red", "#FF0000"), ("Blue", "#0000FF"),
    ("Green", "#008000"), ("Yellow", "#FFFF00"), ("Purple", "#8000FF")
]
for label, color in quick_colors:
    btn = make_button(toolbar2, label, lambda c=color: set_color(c), bg=color)
    btn.config(fg="white" if label in ("Black", "Blue", "Purple") else TEXT_COLOR,
               activebackground=color)
    btn.pack(side="left", padx=3)

undo_button = make_button(toolbar2, "Undo", undo)
undo_button.pack(side="left", padx=(18, 3))
make_button(toolbar2, "Clear", clear_canvas).pack(side="left", padx=3)
make_button(toolbar2, "Open", open_image).pack(side="left", padx=3)
make_button(toolbar2, "Save", save_image).pack(side="left", padx=3)

canvas_frame = tk.Frame(root, bg=PEACH_BUTTON, padx=5, pady=5)
canvas_frame.pack(padx=18, pady=10)
canvas = tk.Canvas(canvas_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                   bg="white", cursor="cross", highlightthickness=0)
canvas.pack()

status_label = tk.Label(root, text="Ready — choose a tool and start drawing",
    bg=PEACH_BG, fg=TEXT_COLOR, font=("Arial", 10))
status_label.pack(pady=(0, 8))

canvas.bind("<Button-1>", start_drawing)
canvas.bind("<B1-Motion>", draw_motion)
canvas.bind("<ButtonRelease-1>", finish_drawing)
refresh_canvas()
update_undo_button()
root.mainloop()