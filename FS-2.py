import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import urllib.request
import urllib.error
from urllib import parse
import socket
from bs4 import BeautifulSoup
import cloudscraper
import re

def open_url(url):
    """Fetches and returns the HTML content of the given URL using a cloudscraper."""
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url).text
    html = BeautifulSoup(resp, "lxml")
    return html

def get_magnet(html):
    """Extracts and returns magnet links along with their details from the HTML content."""
    magnet_pattern = r'<a href="(magnet:\?xt=urn:btih:[^"]+)'
    name_pattern = r'<td class="name">([^<]+)'
    size_pattern = r'<td class="size">([^<]+)'
    date_pattern = r'<td class="date">([^<]+)'
    content = []
    magnets = re.findall(magnet_pattern, str(html))
    names = re.findall(name_pattern, str(html))
    sizes = re.findall(size_pattern, str(html))
    dates = re.findall(date_pattern, str(html))

    for index, magnet in enumerate(magnets):
        content.append(f'{index+1}. 资源名：{names[index]}       种子大小：{sizes[index]}       资源时间：{dates[index]}\n下载链接：{magnet}\n')
    return '\n'.join(content)

class TorrentSearchApp:
    def __init__(self, master):
        self.master = master
        master.title("Torrent Search")

        # Entry for keywords
        self.entry = tk.Entry(master, width=50)
        self.entry.pack(padx=10, pady=10)

        # Button to trigger search
        self.search_button = tk.Button(master, text="Search", command=self.search)
        self.search_button.pack(padx=10, pady=10)

        # ScrolledText to display results
        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=60, height=20)
        self.text_area.pack(padx=10, pady=10)

    def search(self):
        keywords = self.entry.get()
        if keywords:
            url = f'https://torkitty.com/search/{parse.quote(keywords)}/'
            try:
                html_content = open_url(url)
                results = get_magnet(html_content)
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert(tk.INSERT, results)
            except (socket.timeout, urllib.error.URLError) as e:
                messagebox.showerror("Error", f"Network error: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        else:
            messagebox.showinfo("Info", "Please enter some keywords to search.")

root = tk.Tk()
app = TorrentSearchApp(root)
root.mainloop()
