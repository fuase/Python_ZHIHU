# login to zhihu
import requests
from bs4 import BeautifulSoup
import ssl
import re
import os
import traceback
import shutil # 为了能够删除非空文件夹
import urllib.parse # 为了用urllib.urlencode来构造url参数
import time

ssl._create_default_https_context = ssl._create_unverified_context


class TBA: # Ten Best Answers
    def __init__(self, url):
        self.s = requests.Session() # 浏览器访问保持的一个时间段
        self.basicUrl = url # 知乎用户的URL
        self.message = {} # 用户的个人信息字典

        # 在E盘创建Python和ZHIHU文件夹
        if os.path.exists('E:\Python') == False:
            os.mkdir('E:\Python')
        if os.path.exists('E:\Python\ZHIHU') == False:
            os.mkdir('E:\Python\ZHIHU')


    def __del__(self):
        self.s.close()
        print("Call Destructor function")

    def getXsrf(self, url):
        '''
        find the _xsrf in the url web page
        return: _xsrf
        '''
        html = self.s.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        inputTag = soup.find_all('input')
        for x in inputTag:
            if len(x['value']) == 32: # _xsrf的长度为32位
                _xsrf = x['value']
                break
        return _xsrf

    def getCaptcha(self):
        captchaUrl = 'http://www.zhihu.com/captcha.gif'
        r = int(time.time()*1000)
        params = {
            'r': r,
            'type': 'login'
        }
        captchaUrl = captchaUrl + '?' + urllib.parse.urlencode(params)

        pic = TBA.getHtml(self, captchaUrl)
        with open ('pic.gif', 'wb') as f:
            f.write(pic.content)

    def loginZhiHu(self):
        url = 'http://www.zhihu.com'
        _xsrf = TBA.getXsrf(self,url) # 在类中成员函数调用成员函数
        password = 'XXX'
        remember_me = 'true'
        email = 'XXX'
        # 下载并打开验证码图片
        TBA.getCaptcha(self)
        os.system('start pic.gif'.encode('gb2312').decode('gb2312'))
        captcha = input('Please input the captcha: ')

        theData = {
            '_xsrf': _xsrf,
            'password': password,
            'remember_me': remember_me,
            'email': email,
            'captcha': captcha
        }
        # 把图片给删掉
        os.system('del pic.gif'.encode('gb2312').decode('gb2312'))

        suburl = '/login/email'
        loginUrl = url + suburl
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
                                Chrome/49.0.2623.110 Safari/537.36'}
        try:
            html = self.s.post(loginUrl, data=theData, headers=header)
            if html.status_code == 200:
                print('Login ' + url +' Success!')
        except Exception as e:
            print(traceback.format_exc())

    def getHtml(self, url):
        html = None
        try:
            html = self.s.get(url)
        except Exception as e:
            print(traceback.format_exc())
        return html

    def getUserMeg(self):
        '''
        To get the detail message of User
        return: message
        '''
        subUrl = '/about'
        detailUrl = self.basicUrl + subUrl
        print(detailUrl)
        html = self.s.get(detailUrl)
        text = html.text
        soup = BeautifulSoup(text, 'html.parser')


        try:
            # find the name
            #先找到div块，再用find来找子tag的a里面的contents。注意：.contents[0]是string,不加索引是list
            name = soup.find_all(attrs={'class':'title-section ellipsis'})[0].find('a').contents[0]
            self.message['name'] = name # 添加到信息字典中

            # 创建用户信息文件夹
            os.chdir('E:\Python\ZHIHU')
            if os.path.exists('E:\Python\ZHIHU\\'+name) == False: # 不存在则创建
                os.mkdir('E:\Python\ZHIHU\\'+name)

            # find the title
            #title = soup.find_all(attrs={'class':'title-section ellipsis'})[0].find('span').contents[0]
            # 对比，一个是获取contents，一个是用正则表达式抠，因为contents有可能变多，所以用正则抓比较好，下同
            ltitle = soup.find_all(attrs={'class':'title-section ellipsis'})[0].find(attrs={'class': 'bio'})
            title = re.findall(r'title="(.+?)">', str(ltitle))
            self.message['title'] = title[0]

            # find the description
            description = soup.find(attrs={'class': 'zm-editable-editor-input description'})
            if description != None: # 有可能存在没有描述的情况
                description = description.contents[0]
            self.message['description'] = description

            # find the number of agree
            agree = re.findall(r'<strong>(.*)</strong> 赞同', text) # 因为用美丽汤比较难抓，就直接用正则表达式，下同
            self.message['agree'] = agree[0]

            # find the number of thank
            thanks = re.findall(r'<strong>(.*)</strong> 感谢', text)
            self.message['thanks'] = thanks[0]

            # find the number of collection
            fav = re.findall(r'<strong>(.*)</strong> 收藏', text)
            self.message['fav'] = fav[0]

            # find the number of share
            share = re.findall(r'<strong>(.*)</strong> 分享', text)
            self.message['share'] = share[0]

            # find the number of followees and followers
            shortBlock = soup.find_all(attrs={'class': 'zm-profile-side-following zg-clear'})[0].find_all('a')
            followees = re.findall(r'<strong>(.*)</strong>', str(shortBlock[0]))
            self.message['followees'] = followees[0] # 用户关注的人
            followers = re.findall(r'<strong>(.*)</strong>', str(shortBlock[1]))
            self.message['followers'] = followers[0] # 关注用户的人

            # find the number of asks, answers, posts, collections, logs，分别对应index 1,2,3,4,5
            shortBlock = soup.find_all(attrs={'class': 'profile-navbar clearfix'})[0].find_all(attrs={'class': 'item'})
            del shortBlock[0] # 删掉第一个无用的
            item = [] # 存储上述5个信息
            for short in shortBlock:
                num = re.findall(r'class="num">(.*)</span>', str(short))
                item.append(num[0])

            self.message['asks'] = item[0] # 提问
            self.message['answers'] = item[1] # 回答
            self.message['posts'] = item[2] # 文章
            self.message['collections'] = item[3] # 收藏
            self.message['logs'] = item[4] # 公共编辑

        except Exception as e:
            print(traceback.format_exc())


    def printUserMeg(self):
        TBA.getUserMeg(self) # 获取用户详细信息
        try:
            # 在文件夹中创建文件
            os.chdir('E:\Python\ZHIHU\\' + self.message['name']) # 进入用户文件夹
            fileName = self.message['name'] + '个人信息.txt'
            with open(fileName, 'w') as f:
                f.writelines('{0}: {1}\n'.format('Name', self.message['name']))
                f.writelines('{0}: {1}\n'.format('Title', self.message['title']))
                f.writelines('{0}: {1}\n'.format('Description', self.message['description']))
                f.writelines('{0}关注了{1}人，被{2}人关注\n'.format(self.message['name'], self.message['followees'], self.message['followers']))
                f.writelines('提问{0}  回答{1}  文章{2}  收藏{3}  公共编辑{4}\n'
                .format(self.message['asks'], self.message['answers'], self.message['posts'], self.message['collections'], self.message['logs']))
                f.writelines('获得{0}赞同\n'.format(self.message['agree']))
                f.writelines('获得{0}感谢\n'.format(self.message['thanks']))
                f.writelines('获得{0}收藏\n'.format(self.message['fav']))
                f.writelines('获得{0}分享\n'.format(self.message['share']))

            os.system('start ' + fileName.encode('gb2312').decode('gb2312')) # 打开该txt文件
        except Exception as e:
            print(traceback.format_exc())

    def formHtml(self, question, answer, imgUrlList, localPic):
        '''
        利用传进来的素材生成一个网页
        :param question: 问题
        :param answer:  回答
        :param imgUrlList: 答案源码中的图片URL
        :param localPic: 将网页中的图片URL映射为本地的URL
        :return:
        '''

        try:
            path = 'E:\Python\ZHIHU\\' + self.message['name']
            path += '\\' + question
            answer = str(answer) # 将answer转换为str
            # 再将新的local的图片来代替answer中的图片URL
            for url in imgUrlList:
                replacePath = path + '\\' + localPic[url]
                answer = answer.replace(url, replacePath) # 返回一个新的str

            # 将答案源码中的'data-actualsrc'改为'data-actual src'，不然显示不了图片
            count = answer.count('data-actualsrc') # 计算出在answer中共有多少个要修改的子字符串
            i = 0
            while i != count:
                answer = answer.replace('data-actualsrc', 'data-actual src')
                i += 1

            # 生成网页文件
            os.chdir(path) # 保持是在该文件夹之内
            with open('{0}.html'.format('答案'), 'w', encoding='utf-8') as f:
                f.writelines('<html>\n')
                f.writelines('<meta charset="utf-8" />')
                f.writelines('<body>\n')
                f.writelines(answer)
                f.writelines('</body>\n')
                f.writelines('</html>')


        except Exception as e:
            print(traceback.format_exc())

    def getAnswer(self, url):
        '''
        获取一个具体回答，并以网页形式保存
        url是类似'/question/25533083/answer/31097260'的子url
        方法：
        获取问题，答案，和图片并调用formHtml(question, answer, imgList)
        图片分问题图片和答案图片
        :return:
        '''
        headUrl = 'https://www.zhihu.com'
        detailUrl = headUrl + url # 具体问题的具体答案

        html = TBA.getHtml(self, detailUrl)
        if html == None:
            print('html is None')
        text = html.text
        soup = BeautifulSoup(text, 'html.parser')

        try:
            answer = soup.find_all(attrs={'class': 'zm-editable-content clearfix'})[0] # 获取答案源码

            # 获取要下载的图片URL
            asoup = BeautifulSoup(str(answer), 'html.parser') # 找出待下载的图片URL
            imgUrlList = [] # 获取待下载图片的url
            imgpage = asoup.find_all('img')
            for url in imgpage:
                imgUrlList.append(url['src'])

            # 找出问题名字
            question = soup.find(attrs={'class': 'zm-item-title zm-editable-content'}).find('a').contents[0]

            # 将'//zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg'这些URL加上'https:'，以便下载
            i = 0
            while i != len(imgUrlList):
                if imgUrlList[i] == '//zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg':
                    imgUrlList[i] = 'https:' + imgUrlList[i]
                i += 1

            # 进入图片文件夹
            # 创建答案文件
            path = 'E:\Python\ZHIHU\\' + self.message['name']
            os.chdir(path) # 进入该用户的文件夹

            path += '\\' + question
            if os.path.exists(path) == False: # 如果没有则创建，有的话要先删除旧的再建新的
                os.mkdir(path) # 创建以问题命名的文件夹
            else:
                shutil.rmtree(path) # 删除非空文件夹(旧)
                os.mkdir(path) # 创建以问题命名的文件夹(新)
            os.chdir(path) # 进入该问题文件夹

            # 下载图片
            imgCount = 0
            while imgCount != len(imgUrlList):
                binary = TBA.getHtml(self, imgUrlList[imgCount])
                if binary == None:
                    print('binary is None')
                with open('a_{0}.jpg'.format(str(imgCount)), 'wb') as f:
                    f.write(binary.content)
                print('正在下载图片X{0}'.format(str(imgCount + 1)))
                imgCount += 1
            print('下载图片完成！')

             # 将imgList中的'https://zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg'改回来
            # 这样才能替换源码中的URL
            i = 0
            while i != len(imgUrlList):
                if imgUrlList[i] == 'https://zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg':
                    imgUrlList[i] = imgUrlList[i].replace('https://zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg',
                                                          '//zhstatic.zhihu.com/assets/zhihu/ztext/whitedot.jpg')
                i += 1


            localPic = {} # 将网页中的答案图片URL映射为本地的URL
            i = 0
            for url in imgUrlList:
                localPic[url] = 'a_{0}.jpg'.format(str(i))
                i += 1


            TBA.formHtml(self, question, answer, imgUrlList, localPic) # 生成网页

        except Exception as e:
            print(traceback.format_exc())

    def getAnswers(self, n):
        '''
        获取该用户回答的答案，共n个，根据排名高低来获取回答。
        如果n比客户当前回答数要多，那么n就为当前回答数
        :param n: 要获取n个回答
        :return: None
        '''

        # 首先检测n是否大于用户当前的回答数
        n = int(n)
        if n > int(self.message['answers']):
            n = int(self.message['answers'])
            print('要求获取的问题个数大于用户所回答的问题个数')

        if n <= 20:
            lastPage = 1
        else :
            lastPage = int(n / 20) + 1 # 每一页有20个答案，共要抓多少页
        lpac = n % 20 # 最后一页该抓多少个答案, lastPageAnswerCount

        pageNum = 1
        subUrl = '/answers'
        params = {
            'order_by': 'vote_num',
            'page': pageNum
                  }
        questionList = [] # 存储问题的子url

        # 获取到(lastPage)页的全部url
        while pageNum != lastPage + 1:
            params['page'] = pageNum
            url = self.basicUrl +  subUrl + '?' + urllib.parse.urlencode(params)
            html = TBA.getHtml(self, url)

            # 解析并找出20个子问题url
            soup = BeautifulSoup(html.text, 'html.parser')
            everyBlock = soup.find_all('div', attrs={'class': 'zm-item-rich-text js-collapse-body'})
            for each in everyBlock:
                questionList.append(each['data-entry-url']) # 添加子url到问题列表中

            pageNum += 1

        # 将questionList的url减少至20*(lastPage-1)+lpac个
        questionList = questionList[0: (20 * (lastPage - 1) + lpac)]

        # 逐个调用getAnswer()函数，生成n个答案
        for each in questionList:
            TBA.getAnswer(self, each)


if __name__ == '__main__':
    tba = TBA('https://www.zhihu.com/people/XXX')
    tba.loginZhiHu()
    tba.printUserMeg()
    tba.getAnswers(10)





