import tkinter as tk
from tkinter import ttk
import threading
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from tkinter import messagebox

class NewsGUI:

    def __init__(self):
        self.app = tk.Tk()
        self.app.title("News Scraper")
        self.app.geometry("900x600")
        self.data = []
        self.stop_scraping = False

        # menyimpan data hasil scraping
        self.data = []

        # TITLE
        title = tk.Label(
            self.app,
            text="News Scraper",
            font=("Arial", 30, "bold")
        )
        title.pack(pady=20)

        # INPUT URL
        self.url_entry = tk.Entry(self.app, width=60, fg="grey")
        self.url_entry.insert(0, "Enter news website URL...")
        self.url_entry.pack(pady=10)

        # event
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)


        button_frame = tk.Frame(self.app)
        button_frame.pack(padx=10)
        # BUTTON START
        self.start_button = tk.Button(
            button_frame,
            text="Start Scraping",
            width=20,
            command=self.start_scraping
        )
        self.start_button.pack(side="left", pady=10)

        # BUTTON CANCEL
        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel Scraping",
            width=20,
            command=self.cancel_scraping
        )
        self.cancel_button.pack(side="left", pady=10)

        # PROGRESS BAR
        progress_frame = tk.Frame(self.app)
        progress_frame.pack(padx=10)
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal",
                                        length=600, mode="determinate")
        self.progress.pack(side="left")
        self.progress_label = tk.Label(progress_frame, text="0%", width=5)
        self.progress_label.pack(side="left", padx=10)
        
        # FRAME EXPORT
        export_frame = tk.Frame(self.app)
        export_frame.pack(side="bottom", pady=10)

        self.csv_button = tk.Button(
            export_frame,
            text="Export CSV",
            width=15,
            command=self.export_csv
        )
        self.csv_button.pack(side="left", padx=10)

        self.xlsx_button = tk.Button(
            export_frame,
            text="Export Excel",
            width=15,
            command=self.export_excel
        )
        self.xlsx_button.pack(side="left", padx=10)

        # FRAME TABLE
        table_frame = tk.Frame(self.app)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # TREEVIEW
        self.table = ttk.Treeview(
            table_frame,
            columns=("Title", "Date", "Content"),
            show="headings"
        )

        # HEADER
        self.table.heading("Title", text="Title")
        self.table.heading("Date", text="Date")
        self.table.heading("Content", text="Content")

        # COLUMN WIDTH (statis)
        self.table.column("Title", width=150, minwidth=100, stretch=True)
        self.table.column("Date", width=120, minwidth=80, stretch=False)
        self.table.column("Content", width=450, minwidth=200, stretch=True)

        # SCROLLBAR
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscroll=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)

        self.app.mainloop()

    def start_scraping(self):

        self.stop_scraping = False

        thread = threading.Thread(target=self.scrape_worker)
        thread.start()
        for row in self.table.get_children():
            self.table.delete(row)

        self.data.clear()

    # Thread worker → tidak langsung update GUI
    # def scrape_worker(self):
    def scrape_worker(self):

        total = 20   # jumlah berita simulasi
    
        for i in range(total):
        
            # cek apakah user menekan cancel
            if self.stop_scraping:
                self.app.after(
                    0,
                    messagebox.showwarning,
                    "Stopped",
                    "Scraping cancelled by user."
                )
                return
    
            time.sleep(1)  # simulasi proses scraping
    
            # ======================
            # TEMPLATE DATA BERITA
            # ======================
    
            title = f"News Title {i+1}"
            date = "2026-03-07"
            content = f"This is simulated content for article number {i+1}. " \
                      f"You can replace this later with real scraping results."
    
            # ======================
            # PROGRESS
            # ======================
    
            progress = (i + 1) / total * 100
    
            # ======================
            # UPDATE GUI
            # ======================
    
            self.app.after(
                0,
                self.update_gui,
                title,
                date,
                content,
                progress
            )
    
        # ======================
        # SELESAI
        # ======================
    
        self.app.after(
            0,
            messagebox.showinfo,
            "Finished",
            "Scraping completed!"
        )

    # fungsi update GUI dijalankan di main thread
    def update_gui(self, title, date, content, progress):

        self.progress["value"] = progress
        self.progress_label.config(text=f"{int(progress)}%")

        # batasi panjang content agar tidak terlalu panjang
        short_content = content[:150]

        self.table.insert(
            "",
            "end",
            values=(title, date, short_content)
        )

        self.data.append({
            "Title": title,
            "Date": date,
            "Content": content
        })
    
        #export function 
    def export_csv(self):

        if not self.data:
            messagebox.showwarning("Warning", "No data to export")
            return

        df = pd.DataFrame(self.data)
        df.to_csv("news_result.csv", index=False)

        messagebox.showinfo("Success", "Data exported to CSV")


    def export_excel(self):

        if not self.data:
            messagebox.showwarning("Warning", "No data to export")
            return

        df = pd.DataFrame(self.data)
        df.to_excel("news_result.xlsx", index=False)

        messagebox.showinfo("Success", "Data exported to Excel")

    # placeholder
    def clear_placeholder(self, event):
        if self.url_entry.get() == "Enter news website URL...":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="black")

    def add_placeholder(self, event):
        if self.url_entry.get() == "":
            self.url_entry.insert(0, "Enter news website URL...")
            self.url_entry.config(fg="grey")

    # cancel button
    def cancel_scraping(self):

        self.stop_scraping = True

        from tkinter import messagebox
        messagebox.showwarning("Scraping Stopped", "Scraping dihentikan oleh user.")


if __name__ == "__main__":
    NewsGUI()