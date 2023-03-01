<!-- date=2023-03-01 -->
<span id="busuanzi_container_page_pv" style='display:none'>
    本文阅读量: <span id="busuanzi_value_page_pv"></span> 次
</span>
<br>

# Table-of-contents
[TOC]

## 概述
在游戏服务端技术中,由于大部分游戏服务器为了效率,都实现成带状态服务器,很难通过[灰度发布](https://www.zhihu.com/tardis/sogou/art/62766088
)实现线上热更,因此业务层用脚本+支持热更就是一种常见选择,本文仅讨论游戏服务端lua代码热更方案

## 确定禁止热更的代码文件
* 非业务层代码都禁止热更

## 确定热更规范
为了方便沟通,我们把载入程序中的lua文件称为`模块`,为了方便实现热更,约定`模块`只能返回nil/table,返回nil表示本模块对外暴露的都是全局函数,返回table表示返回`模块对象`,外层通过`模块对象`来调用`模块`提供的方法

## 到底热更了什么东西
运行中的lua虚拟机,我们可以把它的构成简化成: `数据` + 操作数据的若干`函数`。`数据`部分我们不能改变,所谓热更也是指改变`函数`的行为,因此热更的关键就是确保只替换`函数`,不改变`数据`,这里的`数据`包括全局数据、函数闭包依赖的局部变量数据、模块携带的数据。

## 热更方案
### 约定
假定存在A模块,我们把A模块刚被载入程序时的状态称为A0,运行一段时间,依赖数据发生改变后的状态称为A1,我们最终需要热更成的状态称为A2,我们的目的是把A1变成A2
### 热更流程
1. 载入A1,A2模块
2. 收集A1模块所有函数依赖的闭包值,假定为uv1
3. 收集A2模块所有函数依赖的闭包值,假定为uv2
4. 递归uv2,将A2模块所有函数的闭包值绑定为A1模块中同名函数的闭包值
5. 递归A2模块,将A2模块中所有函数替换A1模块中的同名函数,A2模块中新增的值添加到A1模块中
6. 丢弃新模块A2,保留旧模块A1,确保引用A1模块的地方不失效
7. 如果模块中提供了__hotfix函数,触发__hotfix(A1),方便上层做热更后的回调逻辑

[Back to TOC](#table-of-contents)

## [源码](https://github.com/sundream/ggApp/blob/master/gg/base/reload.lua)

## 具体示例
main.lua
```lua
gg = gg or {}
require "reload"

local moduleName = "TestReload"
local t = require(moduleName)
t.func1()
t.func2()
t.data6:func1()
t:dump()
print("=========after change module's data=========")
t.func1 = function ()
    print("change TestReload.func1")
end
t.func2 = function ()
    print("change TestReload.func2")
end
t.data1 = 2
t.data2 = 2.0
t.data3 = "new string"
t.data4 = false
t.data5 = "change nil to string"
t.data6.k1 = 2
t.data6.func1 = function (self)
    print("change TestReload.data6.func1",self.k1)
end
t.changeUpValue("new upvalue")
t.func1()
t.func2()
t.data6:func1()
t:dump()
print("=========after reload=========")
gg.reload(moduleName)
t.func1()
t.func2()
t.data6:func1()
t:dump()
```

TestReload.lua
```lua
local TestReload = {}

function TestReload.func1()
    print("TestReload.func1")
end

TestReload.func2 = function ()
    print("TestReload.func2")
end

TestReload.data1 = 1
TestReload.data2 = 1.0
TestReload.data3 = "string"
TestReload.data4 = true
TestReload.data5 = nil
TestReload.data6 = {
    k1 = 1,
    func1 = function (self)
        print("TestReload.data6.func1",self.k1)
    end
}

TestReload.self = TestReload

local upvalue = "upvalue"

function TestReload.changeUpValue(value)
    upvalue = value
end

function TestReload:dump()
    print("TestReload:dump,data1:",self.data1)
    print("TestReload:dump,data2:",self.data2)
    print("TestReload:dump,data3:",self.data3)
    print("TestReload:dump,data4:",self.data4)
    print("TestReload:dump,data5:",self.data5)
    print("TestReload.dump,upvalue:",upvalue)
end

return TestReload
```
执行: `lua main.lua`将输出
```
TestReload.func1
TestReload.func2
TestReload.data6.func1  1
TestReload:dump,data1:  1
TestReload:dump,data2:  1.0
TestReload:dump,data3:  string
TestReload:dump,data4:  true
TestReload:dump,data5:  nil
TestReload.dump,upvalue:        upvalue
=========after change module's data=========
change TestReload.func1
change TestReload.func2
change TestReload.data6.func1   2
TestReload:dump,data1:  2
TestReload:dump,data2:  2.0
TestReload:dump,data3:  new string
TestReload:dump,data4:  false
TestReload:dump,data5:  change nil to string
TestReload.dump,upvalue:        new upvalue
=========after reload=========
TestReload.func1
TestReload.func2
TestReload.data6.func1  2
TestReload:dump,data1:  2
TestReload:dump,data2:  2.0
TestReload:dump,data3:  new string
TestReload:dump,data4:  false
TestReload:dump,data5:  change nil to string
TestReload.dump,upvalue:        new upvalue
```

[Back to TOC](#table-of-contents)