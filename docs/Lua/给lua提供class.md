<!-- date=2023-02-07 -->
<span id="busuanzi_container_page_pv" style='display:none'>
    本文阅读量: <span id="busuanzi_value_page_pv"></span> 次
</span>
<br>

# Table of Contents
[TOC]

## 概述
lua自身原生不支持面向对象,而主流语言大多都支持面向对象,对于习惯以面向对象思维开发的程序员来说,提供class支持是非常必要的。lua的class实现网上已有很多版本,比如[middleclass](https://github.com/kikito/middleclass)、[quick-cocos2dx-community](https://github.com/u0u0/Quick-Cocos2dx-Community/blob/master/quick/framework/functions.lua#L284),之所有重新造轮子是想支持: 1. 支持多重继承; 2. 支持热更父类直接影响子类 3. 支持继承userdata;这块后续会进一步说明。lua支持__index元方法,允许对象访问不存在的属性时触发调用,因此我们可以利用这个特性实现继承。

## 简版实现
```lua
function class(classname,super)
    local cls = {}
    _G[classname] = cls
    cls.__index = cls
    cls.ctor = false
    cls.super = super
    if super then
        setmetatable(cls,{
            __index = function (cls,k)
                return cls.super[k]
            end
        })
    end
    cls.new = function (...)
        local instance = {}
        setmetatable(instance,cls)
        if cls.ctor then
            cls.ctor(instance,...)
        end
        return instance
    end
    return cls
end

local Point = class("Point")
function Point:ctor(x,y,z)
    self.x = x
    self.y = y
    self.z = z
end

function Point:__tostring()
    return string.format("Point(%s,%s,%s)",self.x,self.y,self.z)
end

local Vector3 = class("Vector3",Point)
function Vector3:ctor(x,y,z)
    Vector3.super.ctor(self,x,y,z)
end

function Vector3:__tostring()
    return string.format("Vector3(%s,%s,%s)",self.x,self.y,self.z)
end

local function test()
    local p1 = Point.new(1,1,1)
    print(p1)
    local v1 = Vector3.new(1,1,1)
    print(v1)
end

test()
```
输出:
```
Point(1,1,1)
Vector3(1,1,1)
```
从实现可知,Vector3并没有定义x,y,z属性,他是从基类Point中继承而来,而__tostring方法已被重写,因此print(v1)调用的是Vector3.__tostring而非Point.__tostring,从效果看来,我们已经实现了一个简版class。那上面实现有什么缺点?,缺点就是当访问父类属性时每次都需要按继承链逐层访问,直到找到属性/一直到根类都找不到属性,这在继承层次深的应用中,访问属性将变得低效,有什么办法可以解决这个问题,答案就是子类中缓存父类属性,比如[云风实现的class](https://blog.codingnow.com/cloud/LuaOO),他为每个类都绑定了一个虚表(vtb),用来缓存自身+继承过来的属性,这样访问父类属性只在第一次访问需要遍历继承链,后续访问都从vtb表中获得。

[Back to TOC](#table-of-contents)

## 我的实现
### 源码
```lua
if not table.new then
    function table.new(narr,nrec)
        return {}
    end
end

local rawget = rawget
local rawset = rawset
local ipairs = ipairs
local pairs = pairs
local getmetatable = getmetatable
local setmetatable = setmetatable
local type = type
local assert = assert

local ggclass = _G

local function _reload_class(name)
    local class_type = assert(ggclass[name],name)
    -- 清空缓存的父类属性
    for k,v in pairs(class_type.__vtb) do
        class_type.__vtb[k] = nil
    end
    class_type.__vtb.__class = class_type
    --print(string.format("reload class,name=%s class_type=%s vtb=%s",name,class_type,vtb))
    return class_type
end

---@brief 分文件定义类
---@param name string 类名
---@return table 类
function partial_class(name)
    local class_type = ggclass[name]
    _reload_class(name)
    for name,_ in pairs(class_type.__children) do
        partial_class(name)
    end
    return class_type
end

local reload_class = partial_class

---@brief 定义类
---@param name string 类名
---@param ... any 若干基类
---@return table 类
function class(name,...)
    local supers = {...}
    local class_type = ggclass[name] or {}
    if not class_type.__children then
        class_type.__children = {}
    end
    if class_type.__supers then
        for _,super_class in ipairs(class_type.__supers) do
            if super_class.__children then
                super_class.__children[name] = nil
            end
        end
    end
    if type(supers[#supers]) == "function" then
        class_type.__create = table.remove(supers,#supers)
    end
    class_type.__supers = {}
    class_type.extend = function (class_type,super_class)
        assert(super_class ~= class_type)
        class_type.__supers[#class_type.__supers+1] = super_class
        if super_class.__children[name] then
            return class_type
        end
        if super_class.__extend then
            super_class.__extend(class_type,super_class)
        end
        super_class.__children[name] = true
        return class_type
    end

    for _,super_class in ipairs(supers) do
        class_type:extend(super_class)
    end
    if DEBUG_CLASS then
        local info = debug.getinfo(2,"S")
        local filename = info.source
        class_type.__filename = filename
    end
    class_type.__name = name
    class_type.super = supers[1]
    class_type.ctor = false
    class_type.__PROPERTY_COUNT = class_type.__PROPERTY_COUNT or 8
    if not ggclass[name] then
        ggclass[name] = class_type
        class_type.__new = function (...)
            local instance = table.new(0,class_type.__PROPERTY_COUNT)
            setmetatable(instance,class_type)
            local create = class_type.__create
            if create then
                -- __create函数返回值一般是个userdata
                instance.__userdata = create(instance,...)
                if class_type.__index == class_type.__vtb then
                    local vtb = class_type.__index
                    class_type.__index = function (instance,k)
                        local v = vtb[k]
                        if v ~= nil then
                            return v
                        end
                        return instance.__userdata[k]
                    end
                end
            end
            return instance
        end
        class_type.new = function (...)
            local instance = class_type.__new(...)
            if class_type.ctor then
                class_type.ctor(instance,...)
            end
            return instance
        end
        class_type.__vtb = {}
        class_type.__index = class_type.__vtb
        local vtb = class_type.__vtb
        setmetatable(class_type,{
            __index = class_type.__vtb,
            __call = function (class_type,...)
                return class_type.new(...)
            end,
            __newindex = function (class_type,k,v)
                rawset(class_type,k,v)
                class_type.__vtb[k] = v
            end
        })
        setmetatable(vtb,{__index = function (vtb,k)
            local result = rawget(class_type,k)
            if result == nil then
                for _,super_type in ipairs(class_type.__supers) do
                    result = super_type[k]
                    if result ~= nil then
                        break
                    end
                end
            end
            if result ~= nil then
                vtb[k] = result
            end
            return result
        end})
    end
    reload_class(name)
    return class_type
end
```

### 支持多重继承
实现多重继承比较简单,访问父类属性时按继承顺序依次遍历父类即可

### 支持热更父类直接影响子类
首先我们要记录继承关系,当父类热更时,递归遍历子类,清空子类的虚表即可实现,具体细节见reload_class函数

### 支持继承userdata
示例:
```c
/*gcc -fPIC --shared -g -O0 -Wall -I/usr/local/include -L/usr/local/lib -o vector3.so lvector3.c */
#include <stdio.h>
#include <stdlib.h>
#include "lua.h"
#include "lauxlib.h"

typedef struct vector3_t {
    float x;
    float y;
    float z;
} vector3_t;

static int
lindex(lua_State *L) {
    vector3_t *v = (vector3_t*)lua_touserdata(L,1);
    const char* key = lua_tostring(L,2);
    switch(key[0]) {
    case 'x':
        lua_pushnumber(L,v->x);
        break;
    case 'y':
        lua_pushnumber(L,v->y);
        break;
    case 'z':
        lua_pushnumber(L,v->z);
        break;
    default:
        abort();
    }
    return 1;
}

static int
lnew_vector3(lua_State *L) {
    float x = lua_tonumber(L,1);
    float y = lua_tonumber(L,2);
    float z = lua_tonumber(L,3);
    vector3_t *v = (vector3_t*)lua_newuserdata(L,sizeof(vector3_t));
    v->x = x;
    v->y = y;
    v->z = z;
    luaL_Reg l[] = {
        {"__index",lindex},
        {NULL,NULL},
    };
    luaL_newlib(L,l);
    lua_setmetatable(L,-2);
    return 1;
}

int
luaopen_vector3_core(lua_State *L) {
    luaL_checkversion(L);
    luaL_Reg l[] = {
        {"new",lnew_vector3},
        {NULL,NULL},
    };
    luaL_newlib(L,l);
    return 1;
}
```
```lua
require "class"
local core = require "vector3.core"

local Vector3 = class("Vector3")

--userdata的构造函数,需要返回userdata,他会绑定到lua实例的__userdata字段
function Vector3:__create(x,y,z)
    local userdata = core.new(x,y,z)
    return userdata
end

function Vector3:__tostring()
    -- self.x <=> self.__userdata.x
    return string.format("Vector3(%s,%s,%s)",self.x,self.y,self.z)
end

function Vector3:__add(p2)
    local p1 = self
    local result = Vector3.new(p1.x+p2.x,p1.y+p2.y,p1.z+p2.z)
    return result
end

local function test()
    local v1 = Vector3.new(1,1,1)
    local v2 = Vector3(2,2,2)
    local v3 = v1 + v2
    print(string.format("%s + %s = %s",v1,v2,v3))
end

test()
```
输出:
```
Vector3(1.0,1.0,1.0) + Vector3(2.0,2.0,2.0) = Vector3(3.0,3.0,3.0)
```

### 一般用法
示例:
```lua
require "class"

local Point = class("Point")
function Point:ctor(x,y,z)
    self.x = x
    self.y = y
    self.z = z
end

local LuaVector3 = class("LuaVector3",Point)

function LuaVector3:ctor(x,y,z)
    LuaVector3.super.ctor(self,x,y,z)
end

function LuaVector3:__add(p2)
    local p1 = self
    local result = LuaVector3.new(p1.x+p2.x,p1.y+p2.y,p1.z+p2.z)
    return result
end

function LuaVector3:__tostring()
    return string.format("[%s,%s,%s]",self.x,self.y,self.z)
end

local function test()
    local p1 = LuaVector3.new(1,1,1)
    local p2 = LuaVector3.new(2,2,2)
    local p3 = p1 + p2
    print(string.format("%s + %s = %s",p1,p2,p3))
    print(string.format("p1.x=%s,p1.y=%s,p1.z=%s",p1.x,p1.y,p1.z))

    local p4 = LuaVector3(1,1,1)
    print(string.format("p4.x=%s,p4.y=%s,p4.z=%s",p4.x,p4.y,p4.z))
end

test()
```
输出:
```
[1,1,1] + [2,2,2] = [3,3,3]
p1.x=1,p1.y=1,p1.z=1
p4.x=1,p4.y=1,p4.z=1
```

[Back to TOC](#table-of-contents)