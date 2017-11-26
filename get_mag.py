import easygui as g
import urllib.request
import urllib.error
import re
from urllib import parse
import socket

def open_url(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')
    response = urllib.request.urlopen(req,timeout=20)
    html = response.read().decode('utf-8')
    return html

def get_magnet(html):
    p = r'<a href="(magnet:\?xt=urn:btih:[^"]+)'
    name = r'<td class="name">([^<]+)'
    size = r'<td class="size">([^<]+)'
    date = r'<td class="date">([^<]+)'
    content = ['BTC地址：1CyVcZERF5VACGsBwcB3hRVRLzu4WNjGSt\n','ETH地址：0x526dd5d1dc729b4ca6cf5707344dd6fdede7dae0\n','欢迎打赏！\n\n']
    result = re.findall(p,html)
    result_name = re.findall(name,html)
    result_size = re.findall(size, html)
    result_date = re.findall(date, html)
    for num, c in enumerate(result):
        content.append('%d.  %s       %s       %s\t%s\n' % (num + 1,result_name[num],result_size[num],result_date[num],c))
    g.textbox(msg="您查询的关键词对应的磁链如下（请用迅雷等下载软件进行下载，容量为种子大小）:",title="获取磁链V1.2\t   作者：Henry\t", text=content)

if __name__ == '__main__':
    while 1:
        fh = g.enterbox(msg='请输入关键词： ',title="获取磁链V1.2\t   作者：Henry\t")
        if fh == None :
            exit(1)
        url = 'https://www.torrentkitty.tv/search/' + parse.quote(fh)+'/'
        try:
            get_magnet(open_url(url))
        except (socket.timeout,urllib.error.URLError):
            g.textbox(msg='错误信息',title="获取磁链V1.2\t   作者：Henry\t", text='已超时，请重试！')
        choices = g.ccbox(msg='是否需要继续查找',choices=('是','否'),title="获取磁链V1.2\t   作者：Henry\t",)
        if choices: pass
        else:
            break
