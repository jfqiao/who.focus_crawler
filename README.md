# who.focus_crawler

**西瓜爬公众号文章流程**
1. 登录网页版的西瓜账号，取cookie的值,将cookie的值替换到xi_gua_crawler_xls.py文件夹中，运行文件即可。
2. 上一步运行的结果会得到一个xls文件，该文件保存在xi_gua_articles文件夹下，将该路径作为参数，输入到wechat_crawler.py文件中运行
3. 运行的结果保存在write_article_dirs下，文件名的格式为年-月-日_时-分-秒，
4. 运行的微信文章保存在wechat_articles_dir文件夹下，具体那一天爬的数据都保存在独立的文件夹下，文件夹命名方式为月_日-时_分
5. 将爬的微信的数据上传到服务器中，路径为/data/who.focus/wechat_articles/


**删除文章状态表的流程**
1. 确定删除的时间，以当前所在的时间为准，会自动替换到需要删除的时间
2. 注意需要在服务器上运行清楚状态的文件。