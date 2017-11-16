import easygui as g
import urllib.request
import re
from urllib import parse
import time

def open_url(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    return html

def get_magnet(html):
    p = r'<a href="(magnet:\?xt=urn:btih:[^"]+)'
    num = 1
    content = []
    result = re.findall(p,html)
    for num, c in enumerate(result):
	content.append('%d.\t%s\n' % (num + 1, c))
    g.textbox(msg="您查询的关键词对应的磁链如下:", text=content)

if __name__ == '__main__':
    while 1:
        fh = g.enterbox(msg='请输入关键词： ',title="获取磁链")
        url = 'https://www.torrentkitty.tv/search/' + parse.quote(fh)+'/'
        get_magnet(open_url(url))
        choices = g.ccbox(msg='是否需要继续查找',choices=('是','否'))
        if choices: pass
        else:
            break
