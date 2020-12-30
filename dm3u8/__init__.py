import os
import requests
# 不显示警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning,InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from Crypto.Cipher import AES
import re
from multiprocessing.pool import ThreadPool

class Dm3u8:
    """
    下载视频到当前目录的download目录下,
    视频保存为temp.mp4,
    只针对AES-128加密
    只解决一层m3u8url的：1.拼接最后一层url,输入以.m3u8结尾的链接  2.拼接host，输入非.m3u8结尾的二级链接
    处理ts链接是完整或者以/开始
    """
    def __init__(self):
        print('下载视频到同级文件夹download目录下,视频保存为temp.mp4\n'
              '只针对AES-128加密,只解决一层m3u8url的：\n1.拼接最后一层url,输入以.m3u8结尾的链接\n'
              '2.拼接host，输入非.m3u8结尾的二级链接处理ts链接是完整或者以/开始\n'
              '***你可以再使用其它脚本把下载好的视频移动到自定义位置')
        self.m3u8_url = input('请输入m3u8_url')
        self.mp4 = 'temp.mp4'
        self.ts = './download'
        self.key = None
        # 拼接请求的ts_url
        if '.m3u8' in self.m3u8_url:
            self.head = self.m3u8_url.rsplit('/', 1)[0]
        else:
            self.head = '/'.join(self.m3u8_url.split('/', 3)[0:3])
        self.headers = {'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; Redmi K30 Pro MIUI/V12.0.5.0.QFKCNXM)'}
        if not os.path.exists(self.ts + '/'):
            os.makedirs(self.ts + '/')
    def get_m3u8_urls(self):
        m3u8_data = requests.get(url=self.m3u8_url, headers=self.headers, verify=False).text
        m3u8_urls = re.findall(r',\n(.*?)\n#EXTINF', m3u8_data)
        # 查找是否为加密视频
        try:
            key_url = re.findall(r'URI="(.*?)"', m3u8_data)[0]
            self.key = self.get_key(key_url)
        except:
            self.key = None
        print(m3u8_urls)
        ts_urls = []
        for ts_url in m3u8_urls:
            if 'http' not in ts_url:
                if ts_url[0] != '/':
                    ts_url = self.head + '/' + ts_url
                else:
                    ts_url = self.head + ts_url
            ts_urls.append(ts_url)
        return ts_urls


    def download_m3u8_ts(self, i):
        filename = self.ts + '/' + str(i + 1) + '.ts'
        if not os.path.exists(filename):
            try:
                response = requests.get(url=ts_urllist[i], verify=False, timeout=6)
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        print('正在下载%s' % filename)
                        print(response.url)
                        # print(response.content)
                        f.write(self.decry(response.content))
                        print('下载%s完成' % filename)
                else:
                    print('下载内容为空，请检查错误')
            except:
                print('下载失败%s' % ts_urllist[i])


    def get_key(self, key_url):
        if len(key_url) == 0:
            return None
        elif 'http' not in key_url:
            key_url = self.head + key_url  # 拼出key解密密钥URL
        key = requests.get(key_url).content
        print("key：", key)
        return key


    def decry(self, data):
        key = self.key
        print(key)
        if key != None:
            cryptor = AES.new(key, AES.MODE_CBC, key)
            return cryptor.decrypt(data)
        else:
            print('未加密')
            return data


    def combine_ts(self, file_count):
        f1 = open(self.ts + '/' + self.mp4, 'ab')
        for i in range(file_count):
            with open(self.ts + '/' + str(i + 1) + '.ts', 'rb')as f2:
                data = f2.read()
                f1.write(data)
        f1.close()


    def run(self):
        global ts_urllist
        ts_urllist = self.get_m3u8_urls()
        ts_url_count = len(ts_urllist)
        # list1 = [[i, ts_urllist[i]] for i in range(ts_url_count)]
        # self.download_m3u8_ts(2)
        sign = 0
        while sign == 0:
            pool = ThreadPool(5)
            pool.map(self.download_m3u8_ts, [i for i in range(ts_url_count)])
            pool.close()
            # pool.join()

            file_count = len(os.listdir(self.ts))
            if file_count == ts_url_count:
                for i in range(file_count):
                    self.combine_ts(i)
                sign = 1
                print('合成完成')


if __name__ == '__main__':
    """
    自定义模块时，代码中可能会报错需要额外安装packaging模块，更新setuptools
    pip install packaging
    pip install --upgrade setuptools
    """
    down = Dm3u8()
    down.run()
