<!-- date=2023-02-03 -->
## 快速开始
1. 全局安装docsify-cli工具,方便本地预览文档
```shell
npm install docsify-cli --global
```

2. 初始化项目
```shell
docsify init .
输入y
```

3. 确定目录结构
```
以docs作为文章根目录
比如我的docs目录结构如下:
├─C
├─C++
├─Go
├─Linux
├─Lua
├─Python
├─Skynet
├─游戏
│  ├─AOI
│  └─行为树
├─生活
├─算法
└─部署
```

5. 添加文章

6. 自动生成侧边栏
```shell
双击gen_sidebar.bat
```

7. 本地预览
```shell
docsify serve .
之后浏览器打开提示的url
```

8. 上传到GitHub
```shell
git add *
git commit -m 'add: docsify搭建静态博客'
git push origin master
```

9. 访问博客
浏览器打开http://github.com/sundream.github.io/blog

## 配置详解
具体见[index.html](https://raw.githubusercontent.com/sundream/blog/master/index.html)

## 参考
- [docsify官网](https://docsify.js.org/#/)
- [侧边栏目录折叠](https://github.com/iPeng6/docsify-sidebar-collapse)
- [复制代码到剪贴板](https://github.com/jperasmus/docsify-copy-code)
- [Docsify PUML](https://github.com/indieatom/docsify-puml)
- [字数统计](https://github.com/827652549/docsify-count)