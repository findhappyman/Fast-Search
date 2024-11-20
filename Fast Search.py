import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from urllib import parse
import cloudscraper
from bs4 import BeautifulSoup
import threading
from functools import lru_cache
import time
from queue import Queue
import pyperclip

TITLE = "快来搜搜 V2.1   作者：Henry Xue   邮箱：kidfullystar@gmail.com"
SEARCH_URL = "https://torkitty.com/search/{}//"
TIMEOUT = 10
MAX_RETRIES = 3
CACHE_SIZE = 100

@lru_cache(maxsize=CACHE_SIZE)
def open_url(url):
    scraper = cloudscraper.create_scraper()
    for attempt in range(MAX_RETRIES):
        try:
            resp = scraper.get(url, timeout=TIMEOUT)
            # 尝试使用多个解析器，提高兼容性
            for parser in ['lxml', 'html.parser', 'html5lib']:
                try:
                    return BeautifulSoup(resp.text, parser)
                except:
                    continue
            # 如果所有解析器都失败，使用默认解析器
            return BeautifulSoup(resp.text)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            time.sleep(1)

def get_magnet(html):
    content = ['ETH 地址：0x00011D3a9091F8e317f1ff3d5DcEEf5dEf77a661\n', '欢迎打赏！\n']
    
    # 优化正则表达式，预编译提高性能
    patterns = {
        'magnet': re.compile(r'<a href="(magnet:\?xt=urn:btih:[^"]+)'),
        'name': re.compile(r'<td class="name">([^<]+)'),
        'size': re.compile(r'<td class="size">([^<]+)'),
        'date': re.compile(r'<td class="date">([^<]+)')
    }
    
    html_str = str(html)
    results = {key: pattern.findall(html_str) for key, pattern in patterns.items()}
    
    for i, magnet in enumerate(results['magnet'], 1):
        content.append(f"\n{i}. 资源名：{results['name'][i-1]}       种子大小：{results['size'][i-1]}       资源时间：{results['date'][i-1]}\n下载链接：\n{magnet}\n")
    
    return content, results['name']

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("800x600")
        self.search_history = []
        self.create_widgets()
        self.queue = Queue()
        self.check_queue()

    def create_widgets(self):
        # 搜索框和按钮
        frame = ttk.Frame(self)
        frame.pack(pady=10)
        
        # 搜索历史下拉框
        self.history_var = tk.StringVar()
        self.history_combo = ttk.Combobox(frame, textvariable=self.history_var, width=47)
        self.history_combo.pack(side=tk.LEFT, padx=5)
        
        search_button = ttk.Button(frame, text="搜索", command=self.start_search)
        search_button.pack(side=tk.LEFT)
        
        # 进度条
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        
        # 结果显示区域
        result_frame = ttk.Frame(self)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=80, height=30)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 右侧按钮区域
        button_frame = ttk.Frame(result_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        copy_button = ttk.Button(button_frame, text="复制选中", command=self.copy_selected)
        copy_button.pack(pady=5)
        
        clear_button = ttk.Button(button_frame, text="清空", command=self.clear_results)
        clear_button.pack(pady=5)

    def start_search(self):
        words = self.history_var.get()
        if not words:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
            
        # 更新搜索历史
        if words not in self.search_history:
            self.search_history.append(words)
            self.history_combo['values'] = self.search_history
            
        # 显示进度条
        self.progress.pack(pady=5)
        self.progress.start()
        
        # 在新线程中执行搜索
        threading.Thread(target=self.search, args=(words,), daemon=True).start()

    def search(self, words):
        url = SEARCH_URL.format(parse.quote(words))
        try:
            content, result_names = get_magnet(open_url(url))
            if not result_names:
                self.queue.put(("error", "未找到相关资源，请尝试其他关键词"))
                return
            self.queue.put(("success", "".join(content)))
        except Exception as e:
            self.queue.put(("error", f"搜索出错：{str(e)}\n请检查网络连接后重试。"))

    def check_queue(self):
        try:
            msg_type, message = self.queue.get_nowait()
            self.progress.stop()
            self.progress.pack_forget()
            
            if msg_type == "error":
                messagebox.showerror("错误", message)
            else:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, message)
        except:
            pass
        finally:
            self.after(100, self.check_queue)

    def copy_selected(self):
        try:
            selected_text = self.result_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            pyperclip.copy(selected_text)
            messagebox.showinfo("提示", "已复制到剪贴板")
        except tk.TclError:
            messagebox.showwarning("警告", "请先选择要复制的内容")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)

def main():
    app = Application()
    app.mainloop()

if __name__ == '__main__':
    main()
