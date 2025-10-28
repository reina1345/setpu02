import customtkinter

# 外観モードとデフォルトカラーテーマを設定
customtkinter.set_appearance_mode("System")  # "System" (デフォルト), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # "blue" (デフォルト), "green", "dark-blue"

# メインウィンドウを作成
app = customtkinter.CTk()
app.title("My App")
app.geometry("400x300")

# ラベルウィジェットを作成
label = customtkinter.CTkLabel(master=app, text="こんにちは、CustomTkinter！")
label.pack(pady=20, padx=20)

# メインループを開始
app.mainloop()
