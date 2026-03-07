import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Import modul lokal buatan tim kalian
from utils import export_to_csv, export_to_excel
from worker import ScraperWorker

class NewsGUI:
    def __init__(self):
        self.app = tk.Tk()
        self.app.title("News Scraper")
        self.app.geometry("900x600")
        
        self.data = []
        self.worker = None

        # TITLE
        title = tk.Label(self.app, text="News Scraper", font=("Arial", 30, "bold"))
        title.pack(pady=20)

        # INPUT URL
        self.url_entry = tk.Entry(self.app, width=60, fg="grey")
        self.url_entry.insert(0, "Enter news website URL...")
        self.url_entry.pack(pady=10)
        
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)

        # BUTTONS
        button_frame = tk.Frame(self.app)
        button_frame.pack(padx=10)
        
        self.start_button = tk.Button(button_frame, text="Start Scraping", width=20, command=self.start_scraping)
        self.start_button.pack(side="left", pady=10, padx=5)

        self.cancel_button = tk.Button(button_frame, text="Cancel Scraping", width=20, command=self.cancel_scraping, state="disabled")
        self.cancel_button.pack(side="left", pady=10, padx=5)

        # PROGRESS BAR
        progress_frame = tk.Frame(self.app)
        progress_frame.pack(padx=10)
        
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(side="left")
        
        self.progress_label = tk.Label(progress_frame, text="0%", width=5)
        self.progress_label.pack(side="left", padx=10)
        
        # EXPORT BUTTONS
        export_frame = tk.Frame(self.app)
        export_frame.pack(side="bottom", pady=10)

        self.csv_button = tk.Button(export_frame, text="Export CSV", width=15, command=self.export_csv)
        self.csv_button.pack(side="left", padx=10)

        self.xlsx_button = tk.Button(export_frame, text="Export Excel", width=15, command=self.export_excel)
        self.xlsx_button.pack(side="left", padx=10)

        # TABLE (TREEVIEW)
        table_frame = tk.Frame(self.app)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.table = ttk.Treeview(table_frame, columns=("Title", "Date", "Content"), show="headings")
        self.table.heading("Title", text="Title")
        self.table.heading("Date", text="Date")
        self.table.heading("Content", text="Content")

        self.table.column("Title", width=200, minwidth=100, stretch=True)
        self.table.column("Date", width=100, minwidth=80, stretch=False)
        self.table.column("Content", width=450, minwidth=200, stretch=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)

        self.app.mainloop()

    # --- CORE LOGIC ---
    def start_scraping(self):
        url = self.url_entry.get()
        if not url or url == "Enter news website URL...":
            messagebox.showwarning("Warning", "Masukkan URL berita yang valid!")
            return

        # Atur ulang UI
        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.data.clear()
        
        for row in self.table.get_children():
            self.table.delete(row)

        # Inisiasi Worker (Jembatan)
        self.worker = ScraperWorker(
            url=url,
            progress_callback=self.update_progress_safe,
            finished_callback=self.on_finished_safe,
            error_callback=self.on_error_safe
        )
        self.worker.start()

    def cancel_scraping(self):
        if self.worker and self.worker.is_alive():
            self.worker.stop()
            self.start_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            messagebox.showwarning("Stopped", "Scraping dibatalkan. Menunggu background task selesai...")

    # --- THREAD-SAFE UI UPDATES ---
    def update_progress_safe(self, progress):
        self.app.after(0, self._update_progress_ui, progress)

    def _update_progress_ui(self, progress):
        self.progress["value"] = progress
        self.progress_label.config(text=f"{int(progress)}%")

    def on_finished_safe(self, results):
        self.app.after(0, self._on_finished_ui, results)

    def _on_finished_ui(self, results):
        self.start_button.config(state="normal")
        self.cancel_button.config(state="disabled")

        if not results:
            messagebox.showwarning("Hasil Kosong", "Tidak ada berita yang ditemukan atau diekstrak.")
            return

        for item in results:
            title = item.get("title", "No Title")
            date = item.get("date", "No Date")
            content = item.get("content", "")
            
            short_content = content[:150] + "..." if len(content) > 150 else content
            
            self.table.insert("", "end", values=(title, date, short_content))
            self.data.append({
                "Title": title,
                "Date": date,
                "Content": content,
                "URL": item.get("url", "")
            })

        messagebox.showinfo("Selesai", f"Scraping selesai! Ditemukan {len(results)} berita.")

    def on_error_safe(self, error_msg):
        self.app.after(0, self._on_error_ui, error_msg)

    def _on_error_ui(self, error_msg):
        self.start_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        messagebox.showerror("Error", f"Terjadi kesalahan pada Scraper:\n{error_msg}")

    # --- EXPORT (Menggunakan utils.py) ---
    def export_csv(self):
        if not self.data:
            messagebox.showwarning("Warning", "Tidak ada data untuk diekspor!")
            return
        if export_to_csv(self.data):
            messagebox.showinfo("Success", "Data berhasil diekspor ke CSV!")

    def export_excel(self):
        if not self.data:
            messagebox.showwarning("Warning", "Tidak ada data untuk diekspor!")
            return
        if export_to_excel(self.data):
            messagebox.showinfo("Success", "Data berhasil diekspor ke Excel!")

    # --- PLACEHOLDERS ---
    def clear_placeholder(self, event):
        if self.url_entry.get() == "Enter news website URL...":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="black")

    def add_placeholder(self, event):
        if self.url_entry.get() == "":
            self.url_entry.insert(0, "Enter news website URL...")
            self.url_entry.config(fg="grey")

if __name__ == "__main__":
    NewsGUI()
