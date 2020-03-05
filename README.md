# PornHub 爬虫

### 环境准备

- Linux 或者 Mac OS 操作系统， Windows 没有运行过可能存在兼容问题
- 系统安装 Python3 , Aria2
- 条件具备可以安装 MySQL

### 使用方法

1. 安装 Python 依赖

`pip install -r requirements.txt`

2. 如果有数据库

MySQL 创建`pornhub`库  
执行 pornhub.sql 文件里的语句

3. settings.py 中配置

`ARIA_TOKEN = ''` 调 Aria2 接口的 token 验证

`CHANNEL_NUMBER = 1` 可以是数字，也可以是 ALL ，代表 channel.txt 文件中取多少行

`DEFAULT_REQUEST_HEADERS` 提取你自己帐号的 Cookie 配置进去

`MODEL_FILTER_LIST` 这是一个 list, 将关注的 porn star 的名字(**url中的名字，跟网页上显示的会有差别**)填进去

其他的配置项可以了解一下 Scrapy 框架

4. lib 目录下的 database.py 配置

如果需要数据库，配置数据库连接

5. Aria2 配置 RPC 服务

需要开启 Aria2 的 RPC 服务，并且配置使用 token 验证，具体配置方法可以网上搜索，有很多范例


### 已实现爬虫

***
**说明：以下的视频下载都需要 Premium 会员**
***

1. 获取 PornHub 的所有片商频道



执行 `scrapy crawl get` 将在项目的目录下创建文件 channel.txt

里边包含所有片商频道

这个是为了下载指定频道视频做准备

2. 下载片商频道的视频

执行 `scrapy crawl all` 将下载 channel.txt 文件中指定的片商的视频

如果只想下载一部分，需要在配置文件中配置好下载多少行的片商

channel.txt 文件每一行都是一个片商的名字

需要注意的是，有的时候你看到的片商名字和 url 中的名字不太一样，需要填写 url 中的名字

3. 下载已关注的 PornStar 的视频

执行 `scrapy crawl myfollow` 将下载你的帐号下关注的所有的 PornStar 的视频

视频不包括 粉丝专属，付费观看 等类型

### 发现的小问题

1.下载视频

发现有的视频(猜测是下载需要另外付费的)链接，
请求的时候只吐给你8M左右的视频流，服务端就关闭了
需要你自己再次请求剩下大小的内容

使用 `requests` `Retrofit` `curl` 等网络库或者命令，会发现只能读取一段数据就结束了
`requests` 不会抛异常，另外两个会抛异常

通过使用 `wget` 发现链接本身是能下载的，但是是因为 `wget` 会在出现错误的时候重试，所以正常下载

在 `Retrofit` 上 catch 异常然后重新请求，会发现不管用

然后使用 `aria2` 下载并打印详细 log 后发现

第一次下载到8M被关闭连接后，通过 `Range` 这个 header 继续下载也是正常的

有鉴于此，还是将下载的工作交给 `aria2` 这种专门的下载工具更合适

2.视频名称重复

发现有的时候，Porn Star 上传的视频的名称会有重名的情况

所以文件名需要改成 `视频名称-viewkey.mp4`
 