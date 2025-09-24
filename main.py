import os
import random
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import winsound

# -----------------------------
# Helper functions
# -----------------------------
def get_picture_folders(base="pictures"):
    """Return a list of subfolders inside the base pictures folder."""
    folders = []
    for root, dirs, _ in os.walk(base):
        for d in dirs:
            folders.append(os.path.join(root, d))
    return folders


def get_all_pictures(base="pictures"):
    """Return all image file paths under base folder."""
    pictures = []
    for root, _, files in os.walk(base):
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                pictures.append(os.path.join(root, f))
    return pictures


def get_pictures_from_folder(folder):
    """Return all image file paths from a specific folder."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
    ]


def get_random_picture(pictures):
    """Pick a random picture from a list."""
    return random.choice(pictures) if pictures else None


def resize_image_keep_aspect(image, max_width, max_height):
    """Resize image to fit within max dimensions while keeping aspect ratio."""
    original_width, original_height = image.size
    ratio = min(max_width / original_width, max_height / original_height)
    new_size = (int(original_width * ratio), int(original_height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


# -----------------------------
# Main Application
# -----------------------------
class PicturesforPainters(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pictures for Painters")

        self.folder_path = "pictures"
        self.registered_start_time = None
        self.timer_id = None
        self.remaining_time = None

        self.set_dynamic_geometry()
        self.create_widgets()

    # -----------------------------
    # Window sizing
    # -----------------------------
    def set_dynamic_geometry(self):
        largest_area = 0
        largest_dimensions = (800, 600)  # fallback default

        for root, _, files in os.walk("pictures"):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        area = width * height
                        if area > largest_area:
                            largest_area = area
                            largest_dimensions = (width, height)
                except Exception:
                    continue

        width, height = largest_dimensions
        self.geometry(f"{int(width/2)}x{int(height/2)}")

    # -----------------------------
    # Widgets
    # -----------------------------
    def create_widgets(self):
        self.time_var = tk.StringVar(value="5")
        self.time_unit = tk.StringVar(value="min")

        # Timer frame
        self.timer_widget_frame = tk.Frame(self)
        self.timer_widget_frame.place(relx=0.5, rely=0.92, anchor="center", relwidth=0.9, relheight=0.05)

        # Picture and folder frames
        self.picture_frame = tk.Frame(self)
        self.folder_frame = tk.Frame(self)
        for frame in (self.picture_frame, self.folder_frame):
            frame.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.9, relheight=0.8)

        self.current_frame = "folder"
        self.folder_frame.tkraise()

        # Timer widgets
        self.time_var_entry = tk.Entry(self.timer_widget_frame, textvariable=self.time_var, width=10)
        self.time_unitdropdown = tk.OptionMenu(self.timer_widget_frame, self.time_unit, "sec", "min")
        self.start_button = tk.Button(self.timer_widget_frame, text="start",
                                      command=lambda: (self.post_picture(), self.start_timer(self.get_timer_input())))
        self.pause_button = tk.Button(self.timer_widget_frame, text="pause", command=self.pause_button_call)

        self.time_var_entry.grid(row=0, column=0)
        self.time_unitdropdown.grid(row=0, column=1)
        self.start_button.grid(row=0, column=2, padx=(10, 0))
        self.pause_button.grid(row=0, column=3)

        # Folder tree
        self.folder_tree = ttk.Treeview(self.folder_frame, show="tree")
        self.folder_tree.insert("", "end", iid="pictures", text="All pictures")
        self.populate_tree(self.folder_tree, "", "pictures")
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)
        self.folder_tree.grid(row=0, column=0, sticky="nsew")

        # Picture label
        self.picture_label = tk.Label(
            self.picture_frame,
            text="Placeholder for picture. Set time and press start.\nIf you want another picture, press start again."
        )
        self.picture_label.grid(row=0, column=0)

    # -----------------------------
    # Picture handling
    # -----------------------------
    def post_picture(self):
        if self.folder_path == "pictures":
            pictures = get_all_pictures()
        else:
            pictures = get_pictures_from_folder(self.folder_path)

        picture_path = get_random_picture(pictures)
        if not picture_path:
            return

        image = Image.open(picture_path)
        resized_image = resize_image_keep_aspect(image, 800, 600)

        self.photo = ImageTk.PhotoImage(resized_image)
        self.picture_label.config(image=self.photo, text="")
        self.picture_label.image = self.photo

        self.current_frame = "folder"
        self.switch_frame()

    # -----------------------------
    # Timer handling
    # -----------------------------
    def get_timer_input(self):
        if ":" in self.time_var.get():
            return None
        time = float(self.time_var.get())
        return time * 60 if self.time_unit.get() == "min" else time

    def start_timer_callback(self):
        if self.timer_id is None:
            self.start_timer(self.remaining_time)

    def start_timer(self, remaining_time=None):
        """Start or resume the timer, ensuring only one instance runs."""
        # Always cancel any existing timer before starting a new one
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

        # Initialize remaining_time if not provided
        if remaining_time is None:
            if not self.registered_start_time:
                self.registered_start_time = self.get_timer_input()
            self.remaining_time = self.registered_start_time
        else:
            self.remaining_time = remaining_time

        # Safety: if no valid time, bail out
        if self.remaining_time is None:
            return

        # Update display
        if self.remaining_time >= 0:
            minutes_left = self.remaining_time // 60
            seconds_left = self.remaining_time % 60
            self.time_var.set(f"{int(minutes_left)}:{int(seconds_left):02d}")

            # Schedule next tick
            self.timer_id = self.after(1000, lambda: self.start_timer(self.remaining_time - 1))
        else:
            self.time_var.set("0:00")
            self.timer_id = None
            self.play_alarm(5)


    def pause_timer(self):
        """Pause the timer safely."""
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def pause_button_call(self):
        """Toggle pause/resume with debounce protection."""
        if self.pause_button.cget("text") == "pause":
            self.pause_timer()
            self.switch_frame()
            self.pause_button.config(text="resume")
        else:
            # Resume only if no timer is running
            if self.timer_id is None:
                self.start_timer(self.remaining_time)
            self.switch_frame()
            self.pause_button.config(text="pause")

    # -----------------------------
    # Folder tree
    # -----------------------------
    def populate_tree(self, tree, parent, path):
        try:
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    node_id = tree.insert(parent, "end", text=entry, values=[entry_path])
                    self.populate_tree(tree, node_id, entry_path)
        except PermissionError:
            pass

    def on_folder_select(self, event):
        selected_item = self.folder_tree.focus()
        if selected_item and selected_item != "pictures":
            self.folder_path = self.folder_tree.item(selected_item, "values")[0]
        else:
            self.folder_path = "pictures"

    # -----------------------------
    # Frame switching
    # -----------------------------
    def switch_frame(self):
        if self.current_frame == "picture":
            self.folder_frame.tkraise()
            self.current_frame = "folder"
        else:
            self.picture_frame.tkraise()
            self.current_frame = "picture"

    # -----------------------------
    # Play the alarm x times
    # -----------------------------
    def play_alarm(self, count=5):
        """Play the alarm sound 'count' times."""
        sound_path = os.path.join("alarm_sound", "alarm.wav")
        if os.path.exists(sound_path):
            # Play asynchronously so it doesn't freeze the GUI
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            if count > 1:
                # Schedule the next play after the sound finishes (~1 sec typical)
                self.after(1000, lambda: self.play_alarm(count - 1))



if __name__ == "__main__":
    app = PicturesforPainters()
    app.mainloop()