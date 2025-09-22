import os
import platform
import time
try:
    if platform.system() == "Windows":
        import winsound
    else:
        winsound = None
except:
    winsound = None

def play_sound(melody, root):
    if melody and os.path.exists(melody):
        try:
            if winsound and melody.lower().endswith(".wav"):
                winsound.PlaySound(melody, winsound.SND_FILENAME)
                return
            else:
                root.bell()
                return
        except:
            root.bell()
            return
    else:
        root.bell()