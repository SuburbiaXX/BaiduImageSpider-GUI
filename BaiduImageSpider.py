import sys
import os
from PyQt5.QtWidgets import *
import re
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
import time

timeout = 5
socket.setdefaulttimeout(timeout)

class Line(QDialog):
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 30

    def __init__(self, t=0.1):
        super().__init__()
        self.time_sleep = t
        self.ui()

    def ui(self):
        self.resize(600, 400)
        self.setWindowTitle('百度图片获取')
        self.line = QLineEdit(self)
        self.line2 = QLineEdit(self)
        self.line3 = QLineEdit(self)
        # self.line4 = QLineEdit(self)

        lb = QLabel('搜索图片关键字', self)
        lb2 = QLabel('图片数量', self)
        lb3 = QLabel('当前状态', self)

        lb.move(30, 50)
        lb2.move(30, 150)
        lb3.move(30, 250)

        self.line.move(240, 50)
        self.line2.move(240, 150)
        self.line3.move(240, 250)

        self.line.setText('')  # 空白，等待输入关键字
        self.line2.setText('')  # 空白，等待输入图片数目
        self.line3.setText('等待')  # 空白，显示情况

        self.bt1 = QPushButton('开始执行', self)
        self.bt1.move(460, 350)
        self.bt1.clicked.connect(self.Action)

        self.show()

    def Action(self):
        if self.bt1.isEnabled():
            self.line3.setText('执行中,请稍等一会')
            QMessageBox.information(self, '提示信息', '正在执行')

            a = int(self.line2.text())
            self.start(self.line.text(), 1, 1, a)

            QMessageBox.information(self, '提示信息', "文件已保存在当前目录下的: {} 文件夹".format(self.line.text()))
            self.line3.setText('已完成')

    # 获取后缀名
    @staticmethod
    def get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """
        :param string original_cookie:
        :param list cookies:
        :return string:
        """
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result

    # 保存图片
    def save_image(self, rsp_data, word):
        if not os.path.exists("./" + word):
            os.mkdir("./" + word)
        # 判断名字是否重复，获取图片长度
        self.__counter = len(os.listdir('./' + word)) + 1
        for image_info in rsp_data['data']:
            try:
                if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                    continue
                obj_url = image_info['replaceUrl'][0]['ObjUrl']
                thumb_url = image_info['thumbURL']
                url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (
                urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                time.sleep(self.time_sleep)
                suffix = self.get_suffix(obj_url)
                # 指定UA和referrer，减少403
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    ('User-agent',
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'),
                ]
                urllib.request.install_opener(opener)
                # 保存图片
                filepath = './%s/%s' % (word, str(self.__counter) + str(suffix))
                urllib.request.urlretrieve(url, filepath)
                if os.path.getsize(filepath) < 5:
                    # print("下载到了空文件，跳过!")
                    os.unlink(filepath)
                    continue
            except urllib.error.HTTPError as urllib_err:
                # print(urllib_err)
                continue
            except Exception as err:
                time.sleep(1)
                # print(err)
                # print("产生未知错误，放弃保存")
                continue
            else:
                # print("图片+1,已有" + str(self.__counter) + "张图片")
                self.setFocus()
                self.line3.setText("图片+1,已有" + str(self.__counter) + "张图片")
                self.__counter += 1
                QApplication.processEvents()
        return

    # 开始获取
    def get_images(self, word):
        search = urllib.parse.quote(word)
        # pn int 图片数
        pn = self.__start_amount
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
            search, search, str(pn), self.__per_page)
            # 设置header防403
            try:
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'],
                                                                  page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except UnicodeDecodeError as e:
                print(e)
                print('-----UnicodeDecodeErrorurl:', url)
            except urllib.error.URLError as e:
                print(e)
                print("-----urlErrorurl:", url)
            except socket.timeout as e:
                print(e)
                print("-----socket timout:", url)
            else:
                # 解析json
                rsp_data = json.loads(rsp, strict=False)
                if 'data' not in rsp_data:
                    # print("触发了反爬机制，自动重试！")
                    continue
                else:
                    self.save_image(rsp_data, word)
                    # 读取下一页
                    # print("下载下一页")
                    pn += self.__per_page
        # print("下载任务结束")
        return

    def start(self, word, total_page=1, start_page=1, per_page=30):
        """
        爬虫入口
        :param word: 抓取的关键词
        :param total_page: 需要抓取数据页数 总抓取图片数量为 页数 x per_page
        :param start_page:起始页码
        :param per_page: 每页数量
        :return:
        """
        self.__per_page = per_page
        self.__start_amount = (start_page - 1) * self.__per_page
        self.__amount = total_page * self.__per_page + self.__start_amount
        self.get_images(word)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    line = Line(0.05)
    sys.exit(app.exec_())
