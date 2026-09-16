# C++ 内存管理 · 第五讲 other allocator

> 来源：[xubenshan.github.io — 第五讲 other allocator](https://xubenshan.github.io/blog/cpp/C__%E5%86%85%E5%AD%98%E7%AE%A1%E7%90%86/%E7%AC%AC%E4%BA%94%E8%AE%B2other%20allocator.html)
> 作者：小熊 | 2026/7/19

本讲介绍 GNU C++ 中除 `std::allocator` 之外的其它分配器：`array_allocator`、`malloc_allocator`、`debug_allocator`、`pool_allocator`、`bitmap_allocator` 等，重点是 bitmap_allocator。

---

一般我们会把分配器用于容器中，不会自己手动使用分配器分配内存。比如：

```cpp
std::allocator<std::string> alloc;
std::string* p = alloc.allocate(3); //分配3个string大小的内存
alloc.deallocate(p, 3);//释放内存
```

用户在释放内存的时候需要手动输入释放的内存大小，这样很麻烦，用户需要牢记自己当初申请了多大的内存。

而使用容器，不需要手动调用 allocate 和 deallcoate。容器内部会自动帮你调用，你只需要指定使用哪种容器即可，当然也不需要牢记申请的内存大小。

---

## GNU C++ 对 allocator 的描述

![GNU C++ allocator 描述概览](attachments/other-01.png)

![GNU C++ allocator 描述（续）](attachments/other-02.png)

![GNU C++ allocator 描述（续）](attachments/other-03.png)

![array_allocator 描述](attachments/other-04.png)

![array_allocator 描述（续）](attachments/other-05.png)

array_allocator 描述里面大小固定的容器指的是刚开始我就知道这个容器需要的内存大小，不会发生变化。这样子的话一开始就把内存分配好，不要再一个元素分配一次了。`std::array` 是一个容器，内部是一个 C++ 数组。

GNU C++ 描述的 allocator 有好几种，我们重点关注 bitmap_allocator 和 pool_allocator。pool_allocator 已经在第二讲就谈过了。

![GNU C++ 的几种 allocator](attachments/other-06.png)

![VS2013 标准 allocator](attachments/other-07.png)

VS2013 底下的标准 allocator 没有做额外的事情，只是调用全局的 operator new/delete。

![G4.9 标准分配器 stdnew_allocator](attachments/other-08.png)

G4.9 标准分配器是 stdnew_allocator。这个分配器也只是简单调用全局的 operator new/delete。

![_gnu_cxx::malloc_allocator](attachments/other-09.png)

`_gnu_cxx::malloc_allocator` 分配器只是简单调用 malloc 和 free。

`std::array` 本质是静态数组，静态数组没有释放的概念，因为是在栈上创建的，操作系统来管理，不需要我们管理。所以 deallocate 接口只是个摆设，内部没有做任何事情。

我们来看一个具体的例子：创建了一个 array_allocator 对象 myalloc，构造函数传入的参数是 my 数组的地址。那么将来用 allocate 分配内存的时候就会从这个数组中取。比如 myalloc.allocate(1) 代表分配一个 int，就会返回 my 数组第一个元素的首地址。接着 allocate(3) 代表分配 3 个 int，就会返回 my 数组第二个元素的首地址。

![array_allocator 具体例子](attachments/other-10.png)

![动态数组版 array_allocator](attachments/other-11.png)

下面这个用的是动态分配获得的数组，上面那张图是静态数组（不能说是静态分配得到的，只有全局或 static 修饰的数组是静态分配得到的）。

![debug_allocator](attachments/other-12.png)

debug_allocator 就是一个包装，把真正的分配器 `_M_allocator` 包装起来。让分配的内存还多带一个 `_M_extra` 个元素大小的空间，用来记录整个内存的大小。这个没什么用，这个多的东西和 cookie 是一样的作用，我们一直想要去除 cookie，这个分配器反而增加 cookie。

alloc 分配器：内存池的设计。

![alloc 分配器：内存池设计](attachments/other-13.png)

![alloc 分配器（续）](attachments/other-14.png)

![alloc 分配器（续）](attachments/other-15.png)

bitmap allocator，每次只要一个元素大小的内存，会调用 `_M_allocate_single_object`，如果多于一个元素大小，就调用全局的 operator new。

![bitmap allocator](attachments/other-16.png)

bitmap 分配器中的一些概念：

blocks 一个 block 就是用户要的一个元素大小的内存。当然如果是 list 容器，block 是两个指针 + 元素大小。

- bitmap 用来记录 64 个 blocks 的状态。bitmap 每个元素是 unsigned int，4 个字节，也就是 32 位 bit，所以需要 bitmap[0] bitmap[1] 来记录 64 个 blocks 的状态。
- Super-blocks size 指的是去掉红色块以外的大小。

还会有两个指针用来管理 super-blocks。叫做一个单元。

![bitmap 分配器概念：blocks / bitmap / super-blocks](attachments/other-17.png)

![bitmap 概念：mini_vector 管理指针](attachments/other-18.png)

用自定义的 `_mini_vector` 容器来管理指针。里面有三个东西，start 指向头、finish 指向最后一个元素的下一个位置、endofstorage 指向容量的尾巴。（可能有点抽象）

内存分配的行为模式：

![行为模式 1](attachments/other-19.png)

![行为模式 2](attachments/other-20.png)

![行为模式 3](attachments/other-21.png)

![行为模式 4](attachments/other-22.png)

第一个 super block 用完后，会再分配另一个 super block。区块的数量会从 64 增长到 128，所以需要用 bitmap 数组的四个元素来表示 block 的状态。vector 数组会再多一个元素，也就是两个指针，用来管理这个 super block。

![第二个 super block：64 → 128](attachments/other-23.png)

再创建第 3 个 super block。vector 还需要再创建一个元素，元素个数是 3 个。但是容量是两倍增长的，从 2->4。endofstorage 指向容量的尾。

![第三个 super block：vector 扩容](attachments/other-24.png)

vector 的机制：vector 有一个元素，现在再添加一个元素，vector 就会扩容，按 2 倍的速度增长。还会发生复制，把原先的元素拷贝到另一块内存中，在另一块内存中进行增长。

entries 代表的就是两个指针组成的单元，用户创建了很多容器，存储的是不同类型的元素，就算元素大小一样，也需要不同的 entries 来管理。

回收动作：

![回收动作](attachments/other-25.png)

第一个 super block 回收后，下一次再分配 super block 的时候，block 数量会变成 128 个，而不是 512 个。

上张 ppt 还有两个 QA。读一下很好理解。

什么时候会把全回收状态的 super block 释放给操作系统呢。当 mini_vector 的大小超过 64 时，会比较新加入的全回收 super block 和 mini_vector 最大的元素的大小，如果大于，就直接调用 operator delete。如果小于，就把最大的 super block 释放掉。

![全回收释放时机](attachments/other-26.png)

![全回收释放（续）](attachments/other-27.png)

示例：

![示例 1](attachments/other-28.png)

![示例 2](attachments/other-29.png)

---

> 上一篇：第四讲 Loki allocator
