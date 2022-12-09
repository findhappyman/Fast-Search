import easygui as g
import urllib.request
import urllib.error
import re
from urllib import parse
import socket
from bs4 import BeautifulSoup
import cloudscraper

titles = "快来搜搜 V1.2\t   作者：Henry Xue\t  邮箱：kidfullystar@gmail.com" 

def open_url(url):
    scraper = cloudscraper.create_scraper()

    resp = scraper.get(url).text
    # print(scraper.get(url).text)
    html = BeautifulSoup(resp, "lxml")

    # req = urllib.request.Request(url)
    # req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')
    # response = urllib.request.urlopen(req,timeout=20)
    # html = response.read().decode('utf-8')
    return html

def get_magnet(html):
    p = r'<a href="(magnet:\?xt=urn:btih:[^"]+)'
    name = r'<td class="name">([^<]+)'
    size = r'<td class="size">([^<]+)'
    date = r'<td class="date">([^<]+)'
    content = ['ETH 地址：0x00011D3a9091F8e317f1ff3d5DcEEf5dEf77a661\n','欢迎打赏！\n']
    result = re.findall(p,str(html))
    result_name = re.findall(name,str(html))
    result_size = re.findall(size, str(html))
    result_date = re.findall(date, str(html))
    for num, c in enumerate(result):
        content.append('\n%d. 资源名：%s       种子大小：%s       资源时间：%s\n下载链接：\n%s\n' % (num + 1,result_name[num],result_size[num],result_date[num],c))
    return content,result_name

if __name__ == '__main__':
    while 1:
        words = g.enterbox(msg='请输入关键词（多个关键词请用空格分开）： ',title="快来搜搜 V1.2\t   作者：Henry Xue ")
        if words == None :
            exit(1)
        url = r'https://torkitty.com/search/' + parse.quote(words)+ '//'
        try:
            content,result_name = get_magnet(open_url(url))
            if result_name[0] == 0:
                raise IndexError
            g.textbox(msg="您查询的关键词对应的下载链接如下（请将下载链接用Ctrl+C粘贴至Free Download Manager等下载软件进行下载，容量为种子大小，非文件大小）:", title=titles, text=content)
        except (socket.timeout,urllib.error.URLError,IndexError):
            g.textbox(msg='错误信息',title=titles, text='您输入的关键词无法找到资源，请尝试其它关键词，谢谢！')
        choices = g.ccbox(msg='是否需要继续查找',choices=('是','否'),title="快来搜搜 V1.2\t   作者：Henry Xue ")
        if choices: pass
        else:
            break
