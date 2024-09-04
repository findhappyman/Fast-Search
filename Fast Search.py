import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from urllib import parse
import cloudscraper
from bs4 import BeautifulSoup

TITLE = "快来搜搜 V2.0   作者：Henry Xue   邮箱：kidfullystar@gmail.com"
SEARCH_URL = "https://torkitty.com/search/{}//"

def open_url(url):
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url)
    return BeautifulSoup(resp.text, "lxml")

def get_magnet(html):
    content = ['ETH 地址：0x00011D3a9091F8e317f1ff3d5DcEEf5dEf77a661\n', '欢迎打赏！\n']
    patterns = {
        'magnet': r'<a href="(magnet:\?xt=urn:btih:[^"]+)',
        'name': r'<td class="name">([^<]+)',
        'size': r'<td class="size">([^<]+)',
        'date': r'<td class="date">([^<]+)'
    }
    results = {key: re.findall(pattern, str(html)) for key, pattern in patterns.items()}
    
    for i, magnet in enumerate(results['magnet'], 1):
        content.append(f"\n{i}. 资源名：{results['name'][i-1]}       种子大小：{results['size'][i-1]}       资源时间：{results['date'][i-1]}\n下载链接：\n{magnet}\n")
    
    return content, results['name']

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        # 搜索框和按钮
        frame = ttk.Frame(self)
        frame.pack(pady=10)
        self.search_entry = ttk.Entry(frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        search_button = ttk.Button(frame, text="搜索", command=self.search)
        search_button.pack(side=tk.LEFT)

        # 结果显示区域
        self.result_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.result_text.pack(pady=10, padx=10)

    def search(self):
        words = self.search_entry.get()
        if not words:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return

        url = SEARCH_URL.format(parse.quote(words))
        try:
            content, result_names = get_magnet(open_url(url))
            if not result_names:
                raise ValueError("No results found")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "".join(content))
        except Exception as e:
            messagebox.showerror("错误", f"您输入的关键词无法找到资源，请尝试其它关键词，谢谢！\n错误详情: {str(e)}")

def main():
    app = Application()
    app.mainloop()

if __name__ == '__main__':
    main()
