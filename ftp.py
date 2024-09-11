import ftplib
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json

# Словарь для хранения сохраненных соединений
saved_connections = {}

def load_connections():
    global saved_connections
    try:
        with open('connections.json', 'r') as file:
            saved_connections = json.load(file)
    except FileNotFoundError:
        saved_connections = {}

def save_connections():
    with open('connections.json', 'w') as file:
        json.dump(saved_connections, file)

def connect_to_ftp():
    global ftp, current_directory
    host = host_entry.get()
    port = int(port_entry.get())
    user = user_entry.get()
    password = password_entry.get()

    try:
        # Создаем объект FTP_TLS
        ftp = ftplib.FTP_TLS()
        
        # Подключаемся к серверу
        ftp.connect(host, port)
        messagebox.showinfo("Connection", f"Connection to {host}:{port} successfully")
        
        # Входим в систему
        ftp.login(user, password)
        messagebox.showinfo("Login", f"Login as {user}")
        
        # Включаем защищенное соединение
        ftp.prot_p()
        
        # Получаем текущую директорию
        current_directory = ftp.pwd()
        
        # Получаем список файлов и директорий
        update_file_list()
        
        # Показываем список файлов и кнопки
        file_list_container.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
        download_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)
        disconnect_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
        
        # Скрываем кнопки "Save Connection" и "Load Connection"
        save_connection_button.grid_forget()
        load_connection_button.grid_forget()
    
    except ftplib.all_errors as e:
        messagebox.showerror("Connection Error", f"Connection error: {e}")

def disconnect_from_ftp():
    global ftp
    if ftp:
        ftp.quit()
        messagebox.showinfo("Disconnection", "Disconnecting from the server")
        ftp = None
        file_list_container.grid_forget()
        download_button.grid_forget()
        disconnect_button.grid_forget()
        
        # Показываем кнопки "Save Connection" и "Load Connection"
        save_connection_button.grid(row=9, column=0, padx=10, pady=10)
        load_connection_button.grid(row=9, column=1, padx=10, pady=10)

def update_file_list():
    global current_directory
    file_list.delete(0, tk.END)  # Очищаем список файлов
    
    try:
        files = ftp.nlst()
        if not files:
            messagebox.showinfo("No Files", "No files found on the server")
        else:
            for file in files:
                file_list.insert(tk.END, file)
    except ftplib.all_errors as e:
        messagebox.showerror("Directory Error", f"Error listing directory: {e}")

def change_directory(event):
    global current_directory
    selected_item = file_list.get(file_list.curselection())
    if selected_item:
        try:
            ftp.cwd(selected_item)
            current_directory = ftp.pwd()
            update_file_list()
        except ftplib.all_errors as e:
            messagebox.showerror("Directory Error", f"Error changing directory: {e}")
    else:
        messagebox.showwarning("No Directory Selected", "Please select a directory to enter")

def go_back():
    global current_directory
    try:
        ftp.cwd("..")
        current_directory = ftp.pwd()
        update_file_list()
    except ftplib.all_errors as e:
        messagebox.showerror("Directory Error", f"Error going back: {e}")

def download_file():
    selected_file = file_list.get(file_list.curselection())
    if selected_file:
        try:
            with open(selected_file, 'wb') as local_file:
                ftp.retrbinary(f'RETR {selected_file}', local_file.write)
            messagebox.showinfo("Download", f"File {selected_file} downloaded successfully")
            open_file(selected_file)
        except ftplib.all_errors as e:
            messagebox.showerror("Download Error", f"Download error: {e}")
    else:
        messagebox.showwarning("No File Selected", "Please select a file to download")

def open_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        edit_window = tk.Toplevel(root)
        edit_window.title(f"Editing {filename}")
        
        text_area = tk.Text(edit_window, wrap='word', width=80, height=20)
        text_area.pack(padx=10, pady=10)
        text_area.insert(tk.END, content)
        
        save_button = ttk.Button(edit_window, text="Save Changes",
                                 command=lambda: save_file(filename, text_area.get(1.0, tk.END)))
        save_button.pack(pady=10)
    except FileNotFoundError:
        messagebox.showerror("File Error", f"The file {filename} does not exist.")
    except UnicodeDecodeError:
        messagebox.showerror("File Error", f"The file {filename} is not a text file or contains unsupported characters.")

def save_file(filename, content):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        
        with open(filename, 'rb') as file:
            ftp.storbinary(f'STOR {filename}', file)
        
        messagebox.showinfo("Save", f"File {filename} saved successfully")
    except ftplib.all_errors as e:
        messagebox.showerror("Save Error", f"Save error: {e}")

def save_connection():
    name = connection_name_entry.get()
    host = host_entry.get()
    port = port_entry.get()
    user = user_entry.get()
    password = password_entry.get()

    if name and host and port and user and password:
        saved_connections[name] = {
            'host': host,
            'port': port,
            'user': user,
            'password': password
        }
        save_connections()
        messagebox.showinfo("Save Connection", f"Connection '{name}' saved successfully")
    else:
        messagebox.showwarning("Save Connection", "Please fill in all fields")

def load_connection_dialog():
    if not saved_connections:
        messagebox.showwarning("Load Connection", "No saved connections found")
        return

    dialog = tk.Toplevel(root)
    dialog.title("Load Connection")

    listbox = tk.Listbox(dialog, width=50, height=10)
    listbox.pack(padx=10, pady=10)

    for name in saved_connections:
        listbox.insert(tk.END, name)

    def on_double_click(event):
        selected_name = listbox.get(listbox.curselection())
        if selected_name:
            connection = saved_connections[selected_name]
            host_entry.delete(0, tk.END)
            host_entry.insert(0, connection['host'])
            port_entry.delete(0, tk.END)
            port_entry.insert(0, connection['port'])
            user_entry.delete(0, tk.END)
            user_entry.insert(0, connection['user'])
            password_entry.delete(0, tk.END)
            password_entry.insert(0, connection['password'])
            dialog.destroy()

    listbox.bind("<Double-Button-1>", on_double_click)

# Загружаем сохраненные соединения
load_connections()

# Создаем главное окно
root = ttk.Window(themename="cosmo")
root.title("FTP Client")

# Создаем и размещаем элементы интерфейса
ttk.Label(root, text="Host:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
host_entry = ttk.Entry(root, width=30)
host_entry.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(root, text="Port:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
port_entry = ttk.Entry(root, width=30)
port_entry.grid(row=2, column=1, padx=10, pady=10)
port_entry.insert(0, "21")  # Устанавливаем значение по умолчанию

ttk.Label(root, text="User:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
user_entry = ttk.Entry(root, width=30)
user_entry.grid(row=3, column=1, padx=10, pady=10)

ttk.Label(root, text="Password:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
password_entry = ttk.Entry(root, width=30, show="*")
password_entry.grid(row=4, column=1, padx=10, pady=10)

connect_button = ttk.Button(root, text="Connect", command=connect_to_ftp, bootstyle=SUCCESS)
connect_button.grid(row=5, column=0, columnspan=2, padx=10, pady=20)

save_connection_button = ttk.Button(root, text="Save Connection", command=save_connection, bootstyle=PRIMARY)
save_connection_button.grid(row=9, column=0, padx=10, pady=10)

load_connection_button = ttk.Button(root, text="Load Connection", command=load_connection_dialog, bootstyle=PRIMARY)
load_connection_button.grid(row=9, column=1, padx=10, pady=10)

# Контейнер для списка файлов
file_list_container = tk.Frame(root)
file_list = tk.Listbox(file_list_container, width=50, height=10)
file_list.pack(padx=10, pady=10)

# Обработчик двойного щелчка для изменения директории
file_list.bind("<Double-Button-1>", change_directory)

# Кнопка для скачивания и открытия файла
download_button = ttk.Button(root, text="Download and Edit", command=download_file, bootstyle=PRIMARY)

# Кнопка для отключения от сервера
disconnect_button = ttk.Button(root, text="Disconnect", command=disconnect_from_ftp, bootstyle=DANGER)

# Значок для возврата на уровень выше
go_back_icon = tk.Label(file_list_container, text="back", cursor="hand2")
go_back_icon.pack(side=tk.LEFT, padx=5)
go_back_icon.bind("<Button-1>", lambda e: go_back())

# Запускаем главный цикл обработки событий
root.mainloop()