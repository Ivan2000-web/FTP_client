import os
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from itertools import zip_longest
import json
import time
import ftplib

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
    port = port_entry.get()
    user = user_entry.get()
    password = password_entry.get()

    # Проверка на пустые поля
    if not host or not port or not user or not password:
        messagebox.showerror("Input Error", "Please fill in all fields")
        return

    try:
        # Создаем объект FTP_TLS
        ftp = ftplib.FTP_TLS()
        
        # Подключаемся к серверу
        ftp.connect(host, int(port))
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
        
        # Скрываем поля для ввода соединения и кнопку connect
        host_label.grid_forget()
        host_entry.grid_forget()
        port_label.grid_forget()
        port_entry.grid_forget()
        user_label.grid_forget()
        user_entry.grid_forget()
        password_label.grid_forget()
        password_entry.grid_forget()
        connect_button.grid_forget()
        
        # Скрываем кнопки "Save Connection" и "Load Connection"
        save_connection_button.grid_forget()
        load_connection_button.grid_forget()

        # Показываем список файлов и кнопки
        file_list_container.grid(row=1, column=0, columnspan=3, padx=10, pady=10)
        download_button.grid(row=2, column=0, padx=5, pady=10)
        disconnect_button.grid(row=2, column=1, padx=5, pady=10)
        delete_button.grid(row=2, column=2, padx=5, pady=10)  # Добавляем кнопку удаления
    
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
        delete_button.grid_forget()  # Скрываем кнопку удаления

        # Показываем поля для ввода соединения и кнопку connect
        host_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        host_entry.grid(row=1, column=1, padx=10, pady=10)
        port_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        port_entry.grid(row=2, column=1, padx=10, pady=10)
        user_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        user_entry.grid(row=3, column=1, padx=10, pady=10)
        password_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        password_entry.grid(row=4, column=1, padx=10, pady=10)
        connect_button.grid(row=5, column=0, columnspan=2, padx=10, pady=20)

        # Показываем кнопки "Save Connection" и "Load Connection"
        save_connection_button.grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)
        load_connection_button.grid(row=6, column=1, padx=10, pady=10, sticky=tk.E)

def update_file_list():
    global current_directory
    file_list.delete(0, tk.END)  # Очищаем список файлов
    
    try:
        files = ftp.nlst()
        if not files:
            messagebox.showinfo("No Files", "No files found on the server")
        else:
            for file in files:
                try:
                    ftp.cwd(file)
                    ftp.cwd("..")
                    file_list.insert(tk.END, file)
                    file_list.itemconfig(tk.END, {'bg': '#dbffc4'})  # Выделяем папки зеленым цветом
                except ftplib.error_perm:
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
            # Создаем папку download, если она не существует
            if not os.path.exists('download'):
                os.makedirs('download')
            
            # Путь для сохранения файла
            local_file_path = os.path.join('download', selected_file)
            
            with open(local_file_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {selected_file}', local_file.write)
            messagebox.showinfo("Download", f"File {selected_file} downloaded successfully")
            open_file(local_file_path, current_directory, selected_file)
        except ftplib.all_errors as e:
            messagebox.showerror("Download Error", f"Download error: {e}")
    else:
        messagebox.showwarning("No File Selected", "Please select a file to download")

def open_file(filename, original_directory, original_file_path):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Сохраняем первоначальное состояние файла (до изменений в папку before_changes)
        save_original_state(filename)
        
        edit_window = tk.Toplevel(root)
        edit_window.title(f"Editing {filename}")
        
        # Открываем окно на весь экран
        edit_window.state('zoomed')
        
        text_area = tk.Text(edit_window, wrap='word', width=80, height=40, font=("Arial", 12))  # Увеличиваем размер текста
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content)
        
        def save_changes():
            new_content = text_area.get(1.0, tk.END)
            save_file(filename, new_content, original_directory, original_file_path)
            edit_window.destroy()
        
        save_button = ttk.Button(edit_window, text="Save Changes", command=save_changes, bootstyle=PRIMARY)
        save_button.pack(side=tk.BOTTOM, pady=10)  # Размещаем кнопку внизу окна
        
        # Подсветка изменений
        def highlight_changes(event=None):
            new_content = text_area.get(1.0, tk.END)
            if new_content != content:
                text_area.tag_remove("changed", "1.0", tk.END)
                diff_lines = new_content.splitlines()
                original_lines = content.splitlines()
                for i, (new_line, original_line) in enumerate(zip_longest(diff_lines, original_lines, fillvalue='')):
                    if new_line != original_line:
                        start = f"{i+1}.0"
                        end = f"{i+1}.end"
                        text_area.tag_add("changed", start, end)
        
        text_area.tag_configure("changed", background="#ffe6e6")  # Легкий красный цвет для подсветки
        text_area.bind("<KeyRelease>", highlight_changes)
        highlight_changes()
        
        edit_window.update_idletasks()  # Принудительно обновляем окно
        
    except FileNotFoundError:
        messagebox.showerror("File Error", f"The file {filename} does not exist.")
    except UnicodeDecodeError:
        messagebox.showerror("File Error", f"The file {filename} is not a text file or contains unsupported characters.")

#Сохраняем файл в папке before_changes перед открытием его на редактирование
def save_original_state(filename):
    if not os.path.exists('before_changes'):
        os.makedirs('before_changes')
    
    original_file_path = os.path.join('before_changes', os.path.basename(filename))
    with open(filename, 'r', encoding='utf-8') as original_file:
        original_content = original_file.read()
    
    with open(original_file_path, 'w', encoding='utf-8') as original_file:
        original_file.write(original_content)

def save_file(filename, content, original_directory, original_file_path):
    try:
        # Сохраняем изменения в локальный файл
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # Переходим в исходную директорию
        ftp.cwd(original_directory)
        
        # Выгружаем файл на сервер
        with open(filename, 'rb') as file:
            ftp.storbinary(f'STOR {original_file_path}', file)
        
        messagebox.showinfo("Save", f"File {original_file_path} saved successfully")
        
        # Удаляем файл из папки download после успешной выгрузки (из папки before_changes не удаляем)
        os.remove(filename)
        messagebox.showinfo("File Removed", f"File {filename} removed from download folder")
    
    except ftplib.all_errors as e:
        messagebox.showerror("Save Error", f"Save error: {e}")

def save_connection():
    host = host_entry.get()
    port = port_entry.get()
    user = user_entry.get()
    password = password_entry.get()

    # Проверка на пустые поля
    if not host or not port or not user or not password:
        messagebox.showerror("Input Error", "Please fill in all fields")
        return

    # Создаем окно для ввода имени соединения
    save_dialog = tk.Toplevel(root)
    save_dialog.title("Save Connection")

    ttk.Label(save_dialog, text="Connection Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
    connection_name_entry = ttk.Entry(save_dialog, width=30)
    connection_name_entry.grid(row=0, column=1, padx=10, pady=10)

    def save_connection_with_name():
        name = connection_name_entry.get()
        if name:
            saved_connections[name] = {
                'host': host,
                'port': port,
                'user': user,
                'password': password
            }
            save_connections()
            messagebox.showinfo("Save Connection", f"Connection '{name}' saved successfully")
            save_dialog.destroy()
        else:
            messagebox.showwarning("Save Connection", "Please enter a connection name")

    save_button = ttk.Button(save_dialog, text="Save", command=save_connection_with_name, bootstyle=PRIMARY)
    save_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

def load_connection_dialog():
    if not saved_connections:
        messagebox.showwarning("Load Connection", "No saved connections found")
        return

    dialog = tk.Toplevel(root)
    dialog.title("Load Connection")

    listbox = tk.Listbox(dialog, width=50, height=10)
    listbox.pack(padx=8, pady=8)

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

    def delete_connection():
        selected_name = listbox.get(listbox.curselection())
        if selected_name:
            if messagebox.askyesno("Delete Connection", f"Are you sure you want to delete '{selected_name}'?"):
                del saved_connections[selected_name]
                save_connections()
                messagebox.showinfo("Delete Connection", f"Connection '{selected_name}' deleted successfully")
                listbox.delete(tk.ACTIVE)
        else:
            messagebox.showwarning("Delete Connection", "Please select a connection to delete")

    delete_button = ttk.Button(dialog, text="Delete Connection", command=delete_connection, bootstyle=DANGER)
    delete_button.pack(pady=10)

    listbox.bind("<Double-Button-1>", on_double_click)

# Загружаем сохраненные соединения
load_connections()

# Создаем окно приветствия
def show_splash_screen():
    splash_window = tk.Toplevel(root)
    splash_window.title("Splash Screen")
    splash_window.geometry("500x200")
    splash_window.configure(bg="white")
    splash_window.overrideredirect(True)  # Убираем рамку окна

    # Центрируем окно на экране
    splash_window.update_idletasks()
    width = splash_window.winfo_width()
    height = splash_window.winfo_height()
    x = (splash_window.winfo_screenwidth() // 2) - (width // 2)
    y = (splash_window.winfo_screenheight() // 2) - (height // 2)
    splash_window.geometry(f"{width}x{height}+{x}+{y}")

    # Добавляем текст
    label = tk.Label(splash_window, text="MADE BY IVAN POTVOROV", font=("Arial", 24), bg="white")
    label.pack(pady=40)

    # Закрываем окно через 2 секунды
    splash_window.after(2000, splash_window.destroy)

    return splash_window  

# Создаем главное окно
root = ttk.Window(themename="cosmo")
root.title("FTP Client")

# Показываем окно приветствия
splash_window = show_splash_screen() 

# Дожидаемся закрытия окна приветствия перед запуском главного цикла обработки событий
root.wait_window(splash_window)

# Создаем и размещаем элементы интерфейса
host_label = ttk.Label(root, text="Host:", font=("Arial", 12))
host_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
host_entry = ttk.Entry(root, width=30, font=("Arial", 12))
host_entry.grid(row=1, column=1, padx=10, pady=10)

port_label = ttk.Label(root, text="Port:", font=("Arial", 12))
port_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
port_entry = ttk.Entry(root, width=30, font=("Arial", 12))
port_entry.grid(row=2, column=1, padx=10, pady=10)
port_entry.insert(0, "21")  # Устанавливаем значение по умолчанию

user_label = ttk.Label(root, text="User:", font=("Arial", 12))
user_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
user_entry = ttk.Entry(root, width=30, font=("Arial", 12))
user_entry.grid(row=3, column=1, padx=10, pady=10)

password_label = ttk.Label(root, text="Password:", font=("Arial", 12))
password_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
password_entry = ttk.Entry(root, width=30, show="*", font=("Arial", 12))
password_entry.grid(row=4, column=1, padx=10, pady=10)

# Создаем стили для кнопок
style = ttk.Style()
style.configure("Connect.TButton", background="lightgreen", foreground="black", font=("Arial", 10), padding=10, width=16)
style.map("Connect.TButton",
         background=[('active', 'yellow'), ('!active', 'lightgreen')],
         foreground=[('active', 'black'), ('!active', 'black')])

style.configure("Save.TButton", font=("Arial", 10), padding=10, width=20)
style.configure("Load.TButton", font=("Arial", 10), padding=10, width=20)
style.configure("Delete.TButton", background="red", foreground="white", font=("Arial", 10), padding=10, width=20)
style.map("Delete.TButton",
         background=[('active', 'darkred'), ('!active', 'red')],
         foreground=[('active', 'white'), ('!active', 'white')])

connect_button = ttk.Button(root, text="Connect", command=connect_to_ftp, style="Connect.TButton")
connect_button.grid(row=5, column=0, columnspan=2, padx=10, pady=20)

save_connection_button = ttk.Button(root, text="Save Connection", command=save_connection, style="Save.TButton")
save_connection_button.grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)

load_connection_button = ttk.Button(root, text="Load Connection", command=load_connection_dialog, style="Load.TButton")
load_connection_button.grid(row=6, column=1, padx=10, pady=10, sticky=tk.E)

# Контейнер для списка файлов
file_list_container = tk.Frame(root)
file_list = tk.Listbox(file_list_container, width=100, height=25, font=("Arial", 12))
file_list.pack(padx=10, pady=10)

# Обработчик двойного щелчка для изменения директории
file_list.bind("<Double-Button-1>", change_directory)

# Кнопка для скачивания и открытия файла
download_button = ttk.Button(root, text="Download and Edit", command=download_file, style="Save.TButton")

# Кнопка для отключения от сервера
disconnect_button = ttk.Button(root, text="Disconnect", command=disconnect_from_ftp, style="Connect.TButton")

# Значок для возврата на уровень выше
go_back_icon = tk.Label(file_list_container, text="back", cursor="hand2", font=("Arial", 12))
go_back_icon.pack(side=tk.LEFT, padx=5)
go_back_icon.bind("<Button-1>", lambda e: go_back())

# Кнопка для удаления файла или папки
def delete_file_or_directory():
    selected_item = file_list.get(file_list.curselection())
    if selected_item:
        if messagebox.askyesno("Delete Confirmation", f"Are you sure you want to delete '{selected_item}'?"):
            try:
                ftp.delete(selected_item)  # Удаляем файл
                messagebox.showinfo("Delete", f"File {selected_item} deleted successfully")
            except ftplib.error_perm:
                try:
                    ftp.rmd(selected_item)  # Удаляем папку
                    messagebox.showinfo("Delete", f"Directory {selected_item} deleted successfully")
                except ftplib.all_errors as e:
                    messagebox.showerror("Delete Error", f"Error deleting {selected_item}: {e}")
            update_file_list()
    else:
        messagebox.showwarning("No Item Selected", "Please select a file or directory to delete")

delete_button = ttk.Button(root, text="Delete", command=delete_file_or_directory, style="Delete.TButton")

# Запускаем главный цикл обработки событий
root.mainloop()