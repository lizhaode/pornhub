# PornHub Crawler

### Environment Requirement

- System: Mac OS/Linux, Windows never test
- Lanuage: >=Python3.9
- CommandLine Tool: Aria2

### How To Use

1. Install Python Denpendencies

`pip install -r requirements.txt`

2. settings.py configure

`MODEL_LIST` type:list, paste model name to here (**name in url, maybe different with website shown**)

other is the same as Scrapy framework

3. make sure `aria2c` command can be used


### Crawlers

1. Download MODEL's videos
2. Download PORNSTAR's videos

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
 
