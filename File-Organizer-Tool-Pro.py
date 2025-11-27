import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import ctypes
import sys  # EKLENDİ: Sistem yolları için gerekli
from PIL import Image, ImageTk 

# --- BU FONKSİYON ÇOK ÖNEMLİ ---
# Bu fonksiyon, dosya EXE olduğunda resimlerin doğru yerden (temp klasöründen)
# okunmasını sağlar. Normal çalışırken de olduğu yerden okur.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller dosyaları buraya çıkarır
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# -------------------------------

class UltimateFileOrganizer:
    def __init__(self, root):
        try:
            myappid = 'company.fileorganizer.pro.v5' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        self.root = root
        self.root.title("File Organizer Pro - Tam Paket")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        
        # --- Ayarlar (GÜNCELLENDİ) ---
        self.duplicate_folder_name = "Aynı Dosyalar (Duplicates)"
        
        # ARTIK LOGOYU resource_path İLE ÇAĞIRIYORUZ
        self.logo_path = resource_path("logo.png") 
        
        # --- Veri Takibi ---
        self.move_history = [] 
        self.duplicate_count = 0

        # --- Renk Paleti ---
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#009688"
        self.warn_color = "#FF5722"
        self.sec_color = "#3c3f41"

        self.root.configure(bg=self.bg_color)
        
        # --- Stil ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Horizontal.TProgressbar", background=self.accent_color, troughcolor=self.sec_color, bordercolor=self.bg_color)

        # --- LOGO YÜKLEME ---
        self.logo_image = None
        try:
            # A. Pencere İkonu
            icon_img = tk.PhotoImage(file=self.logo_path)
            self.root.iconphoto(True, icon_img)

            # B. Arayüz İçi Logo
            pil_img = Image.open(self.logo_path)
            pil_img = pil_img.resize((80, 80), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Logo hatası: {e}")

        # --- ARAYÜZ ELEMANLARI ---
        header_frame = tk.Frame(root, bg=self.bg_color)
        header_frame.pack(pady=(20, 10))

        if self.logo_image:
            logo_label = tk.Label(header_frame, image=self.logo_image, bg=self.bg_color)
            logo_label.pack(side=tk.TOP, pady=(0, 10))

        tk.Label(header_frame, text="Akıllı Dosya Düzenleyici", bg=self.bg_color, fg=self.accent_color, font=("Segoe UI", 18, "bold")).pack()
        tk.Label(header_frame, text="Otomatik Düzenleme • Her Şey Dahil Sürüm", bg=self.bg_color, fg="#888888", font=("Segoe UI", 9)).pack()

        # Klasör Seçimi
        select_frame = tk.Frame(root, bg=self.bg_color)
        select_frame.pack(pady=10, padx=20, fill="x")

        self.path_entry = tk.Entry(select_frame, bg=self.sec_color, fg=self.fg_color, insertbackground="white", font=("Consolas", 10), relief="flat")
        self.path_entry.pack(side=tk.LEFT, fill="x", expand=True, ipady=8, padx=(0, 10))

        tk.Button(select_frame, text="📁 Klasör Seç", command=self.select_folder, bg="#546E7A", fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(side=tk.LEFT)

        # Log
        self.info_text = tk.Text(root, height=9, bg=self.sec_color, fg="#dddddd", font=("Consolas", 9), state="disabled", relief="flat", padx=10, pady=10)
        self.info_text.pack(padx=20, pady=10, fill="x")

        # Progress
        self.progress = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate", style="Horizontal.TProgressbar")
        self.progress.pack(pady=5)
        self.status_label = tk.Label(root, text="Hazır", bg=self.bg_color, fg="#aaaaaa", font=("Segoe UI", 9))
        self.status_label.pack()

        # Butonlar
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack(pady=20)
        self.run_btn = tk.Button(btn_frame, text="BAŞLAT", command=self.start_thread, bg=self.accent_color, fg="white", font=("Segoe UI", 11, "bold"), relief="flat", width=18, pady=5)
        self.run_btn.pack(side=tk.LEFT, padx=10)
        self.undo_btn = tk.Button(btn_frame, text="↩ GERİ AL", command=self.undo_changes, bg=self.warn_color, fg="white", font=("Segoe UI", 11, "bold"), relief="flat", width=18, pady=5, state="disabled")
        self.undo_btn.pack(side=tk.LEFT, padx=10)

        # Uzantılar
        self.extensions = {
            'Resimler': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.ico'],
            'Belgeler': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx', '.csv', '.rtf', '.odt'],
            'Videolar': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'Müzikler': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'Arşivler': ['.zip', '.rar', '.7z', '.tar', '.gz', '.iso'],
            'Programlar': ['.exe', '.msi', '.dmg', '.pkg', '.py', '.js', '.c', '.cpp', '.java'],
            'Tasarım': ['.psd', '.ai', '.xd', '.sketch', '.blend']
        }

    # --- Yardımcı Metotlar ---
    def log(self, message, tag=None):
        self.info_text.config(state="normal")
        self.info_text.insert(tk.END, message + "\n", tag)
        self.info_text.see(tk.END)
        self.info_text.config(state="disabled")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def start_thread(self):
        self.run_btn.config(state="disabled")
        self.undo_btn.config(state="disabled")
        threading.Thread(target=self.organize_files, daemon=True).start()

    def get_unique_filename(self, target_folder, filename):
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        while os.path.exists(os.path.join(target_folder, new_filename)):
            new_filename = f"{base}_kopya_{counter}{ext}"
            counter += 1
        return new_filename

    def organize_files(self):
        target_dir = self.path_entry.get()
        if not target_dir or not os.path.exists(target_dir):
            messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin!")
            self.run_btn.config(state="normal")
            return

        self.move_history = []
        self.duplicate_count = 0
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        self.log("--- Dosya Analizi Başlıyor ---")
        
        files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
        total_files = len(files)
        
        if total_files == 0:
            self.log("Düzenlenecek dosya bulunamadı.")
            self.run_btn.config(state="normal")
            return

        self.progress["maximum"] = total_files
        self.progress["value"] = 0
        self.info_text.tag_config("dup", foreground="#FF9800")
        self.info_text.tag_config("success", foreground="#4CAF50")
        self.info_text.tag_config("error", foreground="#FF5252")

        for i, filename in enumerate(files):
            time.sleep(0.01)
            source_path = os.path.join(target_dir, filename)
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            category_folder = "Diğer"
            for category, ext_list in self.extensions.items():
                if ext in ext_list:
                    category_folder = category
                    break
            
            main_dest_folder = os.path.join(target_dir, category_folder)
            os.makedirs(main_dest_folder, exist_ok=True)
            main_dest_path = os.path.join(main_dest_folder, filename)
            final_dest_path = ""
            
            if os.path.exists(main_dest_path):
                dup_folder_path = os.path.join(target_dir, self.duplicate_folder_name)
                os.makedirs(dup_folder_path, exist_ok=True)
                unique_name = self.get_unique_filename(dup_folder_path, filename)
                final_dest_path = os.path.join(dup_folder_path, unique_name)
                self.duplicate_count += 1
                log_msg = f"⚠️ Çakışma: {filename} -> {self.duplicate_folder_name}"
                log_tag = "dup"
            else:
                final_dest_path = main_dest_path
                log_msg = f"✅ {filename} -> {category_folder}"
                log_tag = "success"

            try:
                shutil.move(source_path, final_dest_path)
                self.move_history.append({'src': source_path, 'dest': final_dest_path})
                self.log(log_msg, log_tag)
            except Exception as e:
                self.log(f"❌ Hata: {filename} taşınamadı. {e}", "error")

            self.progress["value"] = i + 1
            self.status_label.config(text=f"İşleniyor: {filename} ({i+1}/{total_files})")
            self.root.update_idletasks()

        self.log(f"\n--- İŞLEM TAMAMLANDI ---")
        self.status_label.config(text=f"Bitti. {self.duplicate_count} dosya ayrıştırıldı.")
        self.run_btn.config(state="normal")
        if len(self.move_history) > 0:
            self.undo_btn.config(state="normal")
        if self.duplicate_count > 0:
            messagebox.showinfo("Tamamlandı", f"İşlem bitti.\n\n⚠️ {self.duplicate_count} adet çakışan dosya '{self.duplicate_folder_name}' klasörüne taşındı.")
        else:
            messagebox.showinfo("Başarılı", "Tüm dosyalar kategorize edildi.")

    def undo_changes(self):
        if not self.move_history: return
        if not messagebox.askyesno("Geri Al", "İşlemler geri alınsın mı?"): return
        self.log("\n--- GERİ ALMA ---", "dup")
        self.undo_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.move_history)
        count = 0
        for item in reversed(self.move_history):
            src = item['src']
            dest = item['dest']
            try:
                if os.path.exists(dest):
                    shutil.move(dest, src)
                    count += 1
            except Exception as e:
                self.log(f"Hata: {e}", "error")
            self.progress["value"] += 1
            self.root.update_idletasks()
        self.move_history = []
        self.clean_empty_folders()
        self.log(f"Geri alındı. {count} dosya.", "success")
        self.status_label.config(text="Geri alındı.")
        messagebox.showinfo("Bilgi", "Geri alma tamamlandı.")

    def clean_empty_folders(self):
        target_dir = self.path_entry.get()
        folders_to_check = list(self.extensions.keys()) + [self.duplicate_folder_name, "Diğer"]
        for folder in folders_to_check:
            path = os.path.join(target_dir, folder)
            try:
                if os.path.exists(path) and not os.listdir(path):
                    os.rmdir(path)
            except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateFileOrganizer(root)
    root.mainloop()