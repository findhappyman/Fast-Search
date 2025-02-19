import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import re
from urllib import parse
import cloudscraper
from bs4 import BeautifulSoup
from queue import Queue, Empty

# Constants
TITLE = "快来搜搜 Fast Search V3   作者：Henry   邮箱：findhappyman@gmail.com"
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
        resp = scraper.get(url, timeout=10)  # Add timeout
        if resp.status_code != 200:
            raise ConnectionError(f"服务器返回错误代码: {resp.status_code}")
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        raise ConnectionError(f"无法连接到资源服务器: {str(e)}")

def extract_results(html):
    rows = re.findall(PATTERNS['row'], str(html))
    content = []
    magnets = []  # Store magnet links separately
    for i, row in enumerate(rows, 1):
        magnet = re.search(PATTERNS['magnet'], row)
        name = re.search(PATTERNS['name'], row)
        size = re.search(PATTERNS['size'], row)
        date = re.search(PATTERNS['date'], row)
        if magnet and name and size and date:
            content.append({
                'number': i,
                'name': name.group(1),
                'size': size.group(1),
                'date': date.group(1)
            })
            magnets.append(magnet.group(1))
    return content, magnets

# Tkinter Application
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("900x700")
        self.configure(bg='#2c2c2c')  # 深色背景
        
        # 初始化变量
        self.current_page = 1
        self.loading = False
        self.last_search = ""
        self.magnets = []
        self.all_results = []
        self.displayed_count = 0
        self.sort_column = None
        self.sort_reverse = False
        
        self.create_widgets()
        self.queue = Queue()
        self.check_queue()

    def create_widgets(self):
        # 主容器
        main_container = ttk.Frame(self, style='Dark.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 设置深色主题样式
        style = ttk.Style()
        style.theme_use('clam')  # 使用clam主题以便自定义按钮背景
        style.configure('Dark.TFrame', background='#2c2c2c')
        style.configure('Dark.TLabel', background='#2c2c2c', foreground='white')
        
        # 配置输入框样式
        style.configure('Search.TEntry',
                    fieldbackground='#1e1e1e',
                    foreground='white',
                    insertcolor='white',
                    borderwidth=0,
                    relief='flat',
                    padding=10)
        style.map('Search.TEntry',
                fieldbackground=[('focus', '#333333')],
                lightcolor=[('focus', '#0078D4')],
                bordercolor=[('focus', '#0078D4')])
        
        # 配置按钮样式
        style.configure('Custom.TButton',
                    background='#0078D4',
                    foreground='white',
                    padding=10,
                    font=('Arial', 11))
        
        # 配置Treeview样式
        style.configure("Custom.Treeview",
                    background="#1e1e1e",
                    foreground="#e0e0e0",
                    fieldbackground="#1e1e1e",
                    borderwidth=0,
                    rowheight=40)  # 增加行高
        style.configure("Custom.Treeview.Heading",
                    background="#2c2c2c",
                    foreground="#ffffff",
                    relief="flat",
                    font=('Arial', 11, 'bold'))  # 设置表头字体
        style.map("Custom.Treeview.Heading",
                background=[('active', '#404040')])
        style.map("Custom.Treeview",
                background=[('selected', '#0078D4')],  # 选中行的背景色
                foreground=[('selected', '#ffffff')])  # 选中行的文字颜色
        
        # 搜索区域
        search_frame = ttk.Frame(main_container, style='Dark.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 20))

        # 创建搜索框容器（用于添加边框效果）
        entry_frame = ttk.Frame(search_frame, style='Dark.TFrame')
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 搜索框
        self.search_entry = ttk.Entry(
            entry_frame,
            width=50,
            style='Search.TEntry',
            font=('Arial', 12)
        )
        self.search_entry.pack(fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', self.on_enter)
        
        # 创建边框效果
        def on_entry_focus(event):
            entry_frame.configure(style='Focus.TFrame')
            
        def on_entry_focusout(event):
            entry_frame.configure(style='Dark.TFrame')
            
        # 绑定焦点事件
        self.search_entry.bind('<FocusIn>', on_entry_focus)
        self.search_entry.bind('<FocusOut>', on_entry_focusout)
        
        # 按钮区域
        button_frame = ttk.Frame(search_frame, style='Dark.TFrame')
        button_frame.pack(side=tk.RIGHT)
        
        # 使用 ttk.Button 并统一自定义样式
        search_btn = ttk.Button(
            button_frame,
            text="搜索",
            command=self.start_search,
            style='Custom.TButton'
        )
        search_btn.pack(side=tk.LEFT, padx=5)
        self.search_button = search_btn
        
        clear_btn = ttk.Button(
            button_frame,
            text="清除",
            command=self.clear_search,
            style='Custom.TButton'
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # 进度标签
        self.progress_label = ttk.Label(
            main_container,
            text="",
            style='Dark.TLabel'
        )
        self.progress_label.pack(fill=tk.X, pady=(0, 10))

        # 创建Treeview用于显示结果
        self.result_tree = ttk.Treeview(main_container, 
                                    columns=("name", "size", "date"),  
                                    show="headings",
                                    style="Custom.Treeview",
                                    selectmode="browse")
        
        # 设置列
        self.result_tree.heading("name", text="资源名称", command=lambda: self.sort_by_column("name"))
        self.result_tree.heading("size", text="大小", command=lambda: self.sort_by_column("size"))
        self.result_tree.heading("date", text="时间", command=lambda: self.sort_by_column("date"))
        
        # 设置列宽和对齐方式
        self.result_tree.column("name", width=600, anchor="w")  
        self.result_tree.column("size", width=100, anchor="center")
        self.result_tree.column("date", width=100, anchor="center")
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置Treeview和滚动条
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定单击事件
        self.result_tree.bind('<ButtonRelease-1>', self.on_tree_click)
        
        # 绑定滚动事件
        self.result_tree.bind('<MouseWheel>', self.on_mousewheel)
        self.result_tree.bind('<Button-4>', self.on_mousewheel)
        self.result_tree.bind('<Button-5>', self.on_mousewheel)
        
    def on_enter(self, event):
        self.start_search()

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.progress_label.config(text="")

    def start_search(self):
        search_text = self.search_entry.get().strip()
        if not search_text:
            return
            
        # 重置搜索状态
        self.current_page = 1
        self.last_search = search_text
        self.all_results = []
        self.magnets = []
        self.displayed_count = 0
        
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 显示加载提示
        self.progress_label.config(text="搜索中...")
        
        # 执行搜索
        url = SEARCH_URL.format(search_text)
        try:
            html = open_url(url)
            content, magnets = extract_results(html)
            if not content:
                self.progress_label.config(text="未找到任何资源，请尝试其他关键词。")
                return
                
            # 保存所有结果
            self.all_results = content
            self.magnets = magnets
            
            # 初始显示前20条
            self.load_more_results()
            self.progress_label.config(text="")
            
        except Exception as e:
            self.progress_label.config(text=f"搜索出错: {str(e)}")

    def on_mousewheel(self, event):
        # 检查是否滚动到底部
        if not self.loading and self.all_results:
            tree = event.widget
            
            # 获取可见区域的第一个和最后一个item
            last_visible = tree.identify_row(tree.winfo_height())
            
            if last_visible and last_visible == tree.get_children()[-1]:
                # 如果最后一个可见item是所有items中的最后一个，说明滚动到底部了
                if self.displayed_count < len(self.all_results):
                    self.load_more_results()

    def load_more_results(self):
        if self.loading:
            return
            
        self.loading = True
        start = self.displayed_count
        end = min(start + 20, len(self.all_results))
        
        # 添加新的结果到树形视图
        for idx in range(start, end):
            item = self.all_results[idx]
            values = (
                f"{idx+1}. {item['name']}",
                item['size'],
                item['date']
            )
            self.result_tree.insert("", "end", values=values, tags=(f"magnet_{idx}",))
            self.result_tree.tag_configure(f"magnet_{idx}", foreground="#e0e0e0")
            
        self.displayed_count = end
        self.loading = False
        
        # 如果还有更多结果要加载，尝试加载下一页
        if self.displayed_count >= len(self.all_results) and self.last_search:
            self.current_page += 1
            self.fetch_next_page()
    
    def fetch_next_page(self):
        if not self.loading and self.last_search:
            self.loading = True
            url = SEARCH_URL.format(self.last_search) + str(self.current_page)
            
            try:
                html = open_url(url)
                content, magnets = extract_results(html)
                
                if content:
                    # 添加新的结果到列表
                    self.all_results.extend(content)
                    self.magnets.extend(magnets)
                    self.loading = False
                else:
                    self.loading = False
            except Exception as e:
                print(f"Error fetching next page: {e}")
                self.loading = False

    def on_tree_click(self, event):
        # 获取点击的项
        selection = self.result_tree.selection()
        if selection:
            item = selection[0]
            tags = self.result_tree.item(item)["tags"]
            if tags and tags[0].startswith("magnet_"):
                idx = int(tags[0].split("_")[1])
                if idx < len(self.magnets):
                    self.copy_link(self.magnets[idx])

    def copy_link(self, magnet):
        self.clipboard_clear()
        self.clipboard_append(magnet)
        
        # 创建现代浮动通知
        notification = tk.Toplevel(self)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#0078D4')
        
        # 计算窗口中心位置
        window_x = self.winfo_x()
        window_y = self.winfo_y()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # 将通知框放在窗口底部中间
        notify_width = 200
        notify_height = 30
        x = window_x + (window_width - notify_width) // 2
        y = window_y + window_height - notify_height - 20  # 距离底部20像素
        
        notification.geometry(f"{notify_width}x{notify_height}+{x}+{y}")
        
        # 添加通知内容
        label = tk.Label(
            notification,
            text="✓ 下载链接已复制",
            bg='#0078D4',
            fg='white',
            font=('Arial', 11),
            anchor="center"
        )
        label.pack(expand=True, fill="both", padx=10)
        
        # 淡出效果
        def fade_out():
            alpha = notification.attributes('-alpha')
            if alpha > 0:
                notification.attributes('-alpha', alpha - 0.1)
                self.after(50, fade_out)
            else:
                notification.destroy()
        
        # 1秒后开始淡出
        self.after(2000, fade_out)

    def sort_by_column(self, column):
        # 如果点击的是当前排序列，则反转排序顺序
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
            
        # 更新表头箭头
        for col in ("name", "size", "date"):
            if col == column:
                arrow = " ▼" if self.sort_reverse else " ▲"
                self.result_tree.heading(col, text=self.get_column_title(col) + arrow)
            else:
                self.result_tree.heading(col, text=self.get_column_title(col))
        
        # 排序所有结果
        self.sort_results()
        
        # 重新显示结果
        self.refresh_display()
    
    def get_column_title(self, column):
        titles = {
            "name": "资源名称",
            "size": "大小",
            "date": "时间"
        }
        return titles.get(column, "")
    
    def sort_results(self):
        if not self.all_results:
            return
            
        def get_size_value(size_str):
            # 将大小字符串转换为字节数用于比较
            try:
                number = float(size_str.split()[0])
                unit = size_str.split()[1].upper()
                multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                return number * multipliers.get(unit, 0)
            except:
                return 0
        
        def get_sort_key(item):
            if self.sort_column == "name":
                # 移除序号前缀进行排序
                return item["name"]
            elif self.sort_column == "size":
                return get_size_value(item["size"])
            elif self.sort_column == "date":
                return item["date"]
            return ""
        
        self.all_results.sort(
            key=get_sort_key,
            reverse=self.sort_reverse
        )
        
        # 更新磁力链接列表顺序以保持对应关系
        if self.magnets:
            sorted_indices = [i for i, _ in enumerate(self.all_results)]
            self.magnets = [self.magnets[i] for i in sorted_indices]
    
    def refresh_display(self):
        # 清空当前显示
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 重置显示计数
        self.displayed_count = 0
        
        # 重新加载前20条
        self.load_more_results()
        
    def check_queue(self):
        """Check the queue for any pending messages and update the UI accordingly"""
        try:
            while True:
                # Try to get a message from the queue without blocking
                message = self.queue.get_nowait()
                if isinstance(message, dict):
                    if message.get('type') == 'progress':
                        self.progress_label.config(text=message.get('text', ''))
                    elif message.get('type') == 'results':
                        self.all_results.extend(message.get('results', []))
                        self.magnets.extend(message.get('magnets', []))
                        self.display_results()
                self.queue.task_done()
        except Empty:
            pass
        finally:
            # Schedule the next queue check
            self.after(100, self.check_queue)
        
# Main entry point
def main():
    app = Application()
    app.mainloop()

if __name__ == '__main__':
    main()