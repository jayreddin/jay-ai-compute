import gradio as gr
import threading
import qrcode
from PIL import Image
import io
import tkinter as tk
from tkinter import messagebox

def launch_mobile_server():
    def greet(name):
        return f"Hello {name}!"

    # Create a Gradio interface
    iface = gr.Interface(fn=greet, inputs="text", outputs="text", title="Mobile Interface")

    # Start the Gradio server in a separate thread
    server_thread = threading.Thread(target=iface.launch, kwargs={'server_name': '0.0.0.0', 'server_port': 7860})
    server_thread.start()

    # Generate QR code for the Gradio server
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('http://localhost:7860')
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Display QR code in a popup window
    root = tk.Tk()
    root.title("QR Code")
    root.geometry("300x300")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    img_tk = ImageTk.PhotoImage(Image.open(io.BytesIO(img_byte_arr)))

    label = tk.Label(root, image=img_tk)
    label.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    launch_mobile_server()
