import os
import platform
import tkinter as tk
try:
    if platform.system() == "Windows":
        import winsound
    else:
        winsound = None
except:
    winsound = None

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left", bg="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 8))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    @staticmethod
    def position_dialog(widget):
        # Позиционирование диалога рядом с кнопкой с контролем границ
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        screen_width = widget.winfo_screenwidth()
        screen_height = widget.winfo_screenheight()
        dialog_width = 200
        dialog_height = 150
        if x + dialog_width > screen_width:
            x = screen_width - dialog_width
        if y + dialog_height > screen_height:
            y = widget.winfo_rooty() - dialog_height - 5
        if y < 0:
            y = 0
        return f"{dialog_width}x{dialog_height}+{x}+{y}"


def play_sound(melody, root):
    if melody and os.path.exists(melody):
        try:
            if winsound and melody.lower().endswith(".wav"):
                winsound.PlaySound(melody, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            else:
                root.bell()
                return
        except:
            root.bell()
            return
    else:
        root.bell()