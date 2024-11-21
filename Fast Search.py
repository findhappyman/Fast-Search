import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import re
from urllib import parse
import cloudscraper
from bs4 import BeautifulSoup

# Constants
TITLE = "快来搜搜 V2.0   作者：Henry Xue   邮箱：kidfullystar@gmail.com"
SEARCH_URL = "https://torkitty.net/search/{}//"
PATTERNS = {
    'row': r'<tr>(.*?)</tr>',
    'magnet': r'href="(magnet:\?xt=urn:btih:[^"]+)"',
    'name': r'<td class="name">([^<]+)',
    'size': r'<td class="size">([^<]+)',
    'date': r'<td class="date">([^<]+)'
}

# Scraper functions
def open_url(url):
    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url)
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        raise ConnectionError(f"无法连接到资源服务器: {str(e)}")

def extract_results(html):
    rows = re.findall(PATTERNS['row'], str(html))
    content = []
    for i, row in enumerate(rows, 1):
        magnet = re.search(PATTERNS['magnet'], row)
        name = re.search(PATTERNS['name'], row)
        size = re.search(PATTERNS['size'], row)
        date = re.search(PATTERNS['date'], row)
        if magnet and name and size and date:
            content.append(
                f"\n{i}. 资源名：{name.group(1)}       种子大小：{size.group(1)}       资源时间：{date.group(1)}\n下载链接：\n{magnet.group(1)}\n"
            )
    return content

# Tkinter Application
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        # Search bar and button
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        self.search_entry = ttk.Entry(frame, width=50)
        self.search_entry.grid(row=0, column=0, padx=5, sticky="ew")
        search_button = ttk.Button(frame, text="搜索", command=self.start_search)
        search_button.grid(row=0, column=1, padx=5)
        self.progress_label = ttk.Label(self, text="")
        self.progress_label.grid(row=1, column=0, padx=10, sticky="w")

        # Results display
        self.result_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.result_text.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def start_search(self):
        words = self.search_entry.get().strip()
        if not words:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        self.progress_label.config(text="正在搜索，请稍候...")
        threading.Thread(target=self.search, args=(words,), daemon=True).start()

    def search(self, words):
        url = SEARCH_URL.format(parse.quote(words))
        try:
            html = open_url(url)
            content = extract_results(html)
            if not content:
                raise ValueError("未找到任何资源")
            self.update_results("\n".join(content))
        except Exception as e:
            self.update_results("")
            messagebox.showerror("错误", f"无法找到资源，请尝试其他关键词。\n错误详情: {str(e)}")
        finally:
            self.progress_label.config(text="")

    def update_results(self, content):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, content)

# Main entry point
def main():
    app = Application()
    app.mainloop()

if __name__ == '__main__':
    main()