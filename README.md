# bili-uid-crack B站视频链接UID破解工具

使用在线查询aicu.cc接口或本地运行hashcat和（或）John the Ripper破解B站网页端视频链接或视频分享链接得到视频分享者的UID。

简单地说，在登录B站网页端的情况下，B站视频页面的浏览器地址栏中的链接会自动加上一个`vd_source`参数，点击视频分享按钮时得到的视频分享链接也会有这个参数，这个参数其实是当前用户UID的16进制MD5值，本工具正是通过遍历计算UID的MD5值进行MD5碰撞，最终破解得到UID的。

但是，点击分享按钮得到的链接和浏览器地址栏链接的`vd_source`参数值是不一样的，其原因是两者计算得到MD5的方法不同，前者是UID通过标准的方法计算得到的标准MD5值，而后者是UID通过一种不常规的方法计算得到的非标准MD5值。

本工具支持两种方法破解：

1. 在线调用aicu.cc网站的接口，直接查询MD5对应的UID。但请勿频繁查询aicu.cc接口，否则可能被风控。

2. 在本地离线运行hashcat和（或）John the Ripper进行破解，优先使用hashcat破解，若hashcat不可用则使用John the Ripper破解，但是John the Ripper只能用于破解标准MD5值。

## 运行要求

- python 3.6 或更高版本
- hashcat和（或）John the Ripper

## 使用方法

### 第1步：下载本项目文件

- 方法一：git克隆下载

需要安装git工具，打开命令行运行

```bash
git clone https://github.com/jiarandiana0307/bili-uid-crack.git --depth 1
```

完成克隆后进入项目目录

```bash
cd bili-uid-crack
```

- 方法二：下载项目压缩包

点击[此链接](https://github.com/jiarandiana0307/bili-uid-crack/archive/refs/heads/main.zip)下载项目压缩包，完成后解压。

解压完成后进入项目目录

```bash
cd bili-uid-crack-main
```

### 第2步：安装项目依赖库

在项目根目录运行

```bash
pip install -r requirement.txt
```

### 第3步：下载hashcat和（或）John the Ripper

若仅使用在线查询aicu.cc接口破解UID的功能，则无须下载hashcat和John the Ripper。

优先使用hashcat进行破解，若hashcat不可用可以使用John the Ripper平替。

#### 下载hashcat

若本机已下载hashcat可跳过此步骤。

- 方法一：pip下载（Windows和Linux）

```bash
pip install hashcat
```

- 方法二：hashcat官网下载（Windows和Linux）

进入[https://hashcat.net/hashcat/](https://hashcat.net/hashcat/)，下载最新版二进制文件压缩包，解压并将hashcat目录加入PATH系统环境变量，如果没有添加进环境变量，也可以在后续执行脚本时使用`--hashcat`参数手动指定hashcat程序的路径。

- 方法三：hashcat源码编译下载

在部分运行环境（如Termux）下，官方提供的已编译好的二进制文件可能无法运行，这就需要从源码进行编译下载，步骤参考hashcat的官方编译构建文档：[BUILD.md](https://github.com/hashcat/hashcat/blob/master/BUILD.md)

- 方法四：homebrew下载（MacOS和Linux）

在安装了homebrew后运行

```bash
brew install hashcat
```

- 完成下载后检查hashcat是否能成功运行

获取hashcat版本

```bash
hashcat --version
```

查看可用的计算设备

```bash
hashcat -I
```

如显示无可用计算设备，则hashcat无法正常进行破解，本工具也会无法使用。

若使用英伟达显卡，需要安装与显卡型号对应的[CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)及其对应版本的显卡驱动，才能使用显卡加速破解。

#### 下载John the Ripper（可选）

若hashcat可用则无须下载John the Ripper，若hashcat不可用则可作为hashcat的平替。

但是，John the Ripper只能用于破解标准MD5，也就是说，只能用于破解通过点击视频分享按钮得到的视频分享链接中的MD5，这是因为此工具不支持空字符作为掩码。

可在官网进行下载：[https://www.openwall.com/john/](https://www.openwall.com/john/)。

在Windows系统可以直接在官网下载构建好的程序。其它系统可以下载源码构建编译，构建安装文档见[INSTALL](https://github.com/openwall/john/blob/bleeding-jumbo/doc/INSTALL)。

下载好后，john程序能在`run`文件夹中找到。

### 第4步：运行破解脚本

#### 根据B站链接破解UID

以破解以下视频分享链接为例：

`https://www.bilibili.com/video/BV1vQ4y1Z7C2/?share_source=copy_web&vd_source=c9c39ea43db536f5fc895e71c18e3a48`

- 在线查询aicu.cc接口破解

```bash
python bili_uid_crack_cli.py --aicu --url "https://www.bilibili.com/video/BV1vQ4y1Z7C2/?share_source=copy_web&vd_source=c9c39ea43db536f5fc895e71c18e3a48"
```

注意：请勿频繁查询aicu.cc接口，否则可能被风控。

- 离线本地破解

```bash
python bili_uid_crack_cli.py --url "https://www.bilibili.com/video/BV1vQ4y1Z7C2/?share_source=copy_web&vd_source=c9c39ea43db536f5fc895e71c18e3a48"
```

#### 根据`vd_source`参数MD5值破解UID

`vd_source`参数可能是标准MD5和非标准MD5。以`UID:594527616`为例，其标准MD5是`c9c39ea43db536f5fc895e71c18e3a48`，非标准MD5是`59b2b2238efdc2ce7c9c270be38e38d2`。

- 在线查询aicu.cc接口破解

此方法无须关心`vd_source`参数是否为标准MD5，查询标准MD5或非标准MD5都能得到一样的UID。

```bash
python bili_uid_crack_cli.py --aicu --md5 c9c39ea43db536f5fc895e71c18e3a48
```

注意：此方法仅能查询已存在账号的UID，若查询的MD5对应的UID是一个不存在的B站账号则无法得到结果。而且此方法时效性有限，当有新UID生成但aicu.cc没有及时加入数据库时，也可能会导致无法查询得到结果。

- 离线本地破解

使用离线破解时，MD5的破解分几种情况：

1\. 已知`vd_source`是标准MD5

使用`-s`或`--standard`参数指定传入标准MD5

```bash
python bili_uid_crack_cli.py --md5 c9c39ea43db536f5fc895e71c18e3a48 --standard
```

2\. 已知`vd_source`是非标准MD5

使用`-ns`或`--non-standard`参数指定传入非标准MD5

```bash
python bili_uid_crack_cli.py --md5 59b2b2238efdc2ce7c9c270be38e38d2 --non-standard
```

3\. 不知道`vd_source`是否为标准MD5

```bash
python bili_uid_crack_cli.py --md5 59b2b2238efdc2ce7c9c270be38e38d2
```

当均不使用`--standard`和`--non-standard`参数时，尝试将MD5视为标准MD5和非标准MD5分别进行破解。

开始破解后，脚本会调用hashcat以子程序的方式运行，此时可以通过键盘与hashcat进行交互，按回车可以刷新hashcat运行状态，查看破解速度、进度等信息。

**注意：** 若在已安装CUDA Toolkit及相应驱动的情况下，运行脚本时hashcat报错：

```
nvrtcCompileProgram(): NVRTC_ERROR_INVALID_OPTION

nvrtc: error: invalid value for --gpu-architecture (-arch)

* Device #1: Kernel ./OpenCL/shared.cl build failed.

* Device #1: Kernel ./OpenCL/shared.cl build failed.
```

可以在运行脚本时加上`--backend-ignore-cuda`参数禁用CUDA从而避免报错，例如：

```bash
python bili_uid_crack_cli.py --md5 c9c39ea43db536f5fc895e71c18e3a48 -s --backend-ignore-cuda
```

## 其它用法

- 获取指定UID的MD5值

```bash
python bili_uid_crack_cli.py --uid 594527616
```
得到如下输出：

```bash
获取UID: 594527616 的MD5
标准MD5: c9c39ea43db536f5fc895e71c18e3a48
非标准MD5: 59b2b2238efdc2ce7c9c270be38e38d2
```

- 自定义UID范围进行破解

使用`--range 1 1000000000`参数指定UID在1到1000000000进行破解

```bash
python bili_uid_crack_cli.py --md5 c9c39ea43db536f5fc895e71c18e3a48 --range 1 1000000000
```

为了加快破解速度，本工具内置了目前所有已知的UID号段，囊括了1到10位以及16位的UID，涵盖460,000,000,000个UID，最大UID为3,546,700,000,000,000。所以一般使用默认的UID分布范围就足够了，除非能知道UID位于哪个号段，或想判断UID是否在某个号段内，亦或是B站启用了新的号码段，这就可以使用`--range`参数显式指定UID范围。

工具内置的UID分布范围定义可见于项目根目录`bili_uid_crack`文件夹下的`constants.py`文件。

## 用法及参数

```
usage: bili_uid_crack_cli.py [-h] [-u URL] [-m MD5] [-s] [-ns] [-r RANGE RANGE] [--uid UID] [--hashcat HASHCAT] [--backend-ignore-cuda] [--john JOHN]
                             [--aicu] [-o OUTFILE]
```

```
optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     指定视频URL或视频分享URL。
  -m MD5, --md5 MD5     指定MD5，通过-s和-ns参数指定是否为标准的MD5，若同时提供或都不提供这两个参数，则默认尝试标准和非标准的MD5。
  -s, --standard        传入MD5时，指定MD5来自于视频分享URL或为标准MD5。
  -ns, --non-standard   传入MD5时，指定MD5不是来自于视频分享URL或为非标准的MD5。
  -r RANGE RANGE, --range RANGE RANGE
                        指定破解的UID范围，可以多次使用此参数提供多个范围。缺省时默认尝试所有可能的UID。
  --uid UID             获取指定UID的标准MD5和非标准MD5值。指定此参数时忽略其它参数
  --hashcat HASHCAT     使用指定的hashcat破解程序。
  --backend-ignore-cuda
                        在运行hashcat时忽略CUDA。当使用CUDA导致hashcat运行失败，报错"Kernel ./OpenCL/shared.cl build failed."时可以使用此参数解决。    
  --john JOHN           使用指定的John the Ripper破解程序，注意，若john只能破解标准MD5，无法破解非标准的MD5，也就是说john只能破解在网页端点击视频分享按
钮得到的视频分享链接。
  --aicu                指定直接调用aicu.cc网站的接口查询MD5或URL对应的UID，使用此参数时仅需提供--url或--md5参数即可。通过此方法仅能查询已存在账号的UID，若查询的MD5对应的UID是一个不存在的B站账号则返回结果为空。
  -o OUTFILE, --outfile OUTFILE
                        指定结果的保存路径。
```


## 原理

在登录B站网页端的情况下，B站视频页面的浏览器地址栏中的链接会自动加上一个`vd_source`参数，在网页端点击视频分享按钮时得到的视频分享链接同样会有这个参数，这个参数是当前用户UID的16进制MD5值，可以通过遍历计算UID的MD5值进行MD5碰撞，当计算得到某个UID的MD5值等于链接中的MD5值时，说明这个UID就是此链接的分享者。但是，浏览器地址栏的链接和点击分享按钮得到的链接中的`vd_source`参数的值是不一样的，原因是两者计算得到MD5的方法不同。

在网页端通过点击分享按钮得到的视频分享链接中的`vd_source`参数是UID的标准MD5值，计算方法是先将UID转为字符串，再将字符串逐个字符转为字节数组，比如UID：123得到的字节数组是[0x31, 0x32, 0x33]，计算这个字节数组的16进制MD5值，就得到标准MD5值。

直接在网页端打开视频页面，浏览器地址栏链接中自动添加的`vd_source`参数是UID的非标准MD5值，计算方法是先将UID十进制数中的每一位数字直接放进字节数组，而无须进行字符的转换，例如UID：123，得到的字节数组是[0x01, 0x02, 0x03]，计算这个字节数组的16进制MD5值就得到非标准MD5值。当UID中含有数字0时，字节数组就会有0x00，也就是空字符，而John the Ripper目前不支持空字符，所以John the Ripper无法破解非标准MD5。

通过点击视频分享按钮得到的视频分享链接和浏览器地址栏中的视频链接在查询参数上有明显区别，前者有一个`share_source=copy_web`的参数，而后者没有，通过这一差异可以对两种链接进行区分。

注意，只有通过在网页端登录状态下得到的视频链接才有`vd_source`这一参数，通过APP分享的视频链接是没有的，因而通过APP分享的视频链接无法反推UID，如果用户未登录或手动删除了视频链接的`vd_source`参数也无法反推UID。

## 参考
- [vd_source参数分析](https://www.bilibili.com/opus/1056365185198981142)
- [为什么B站每次打开视频后，URL 后面总会跟一个 vd_source=……？](https://www.zhihu.com/question/558422004/answer/3421476103)
- [B站16位uid对应时间段，截止2025年1月上旬](https://tieba.baidu.com/p/9401456992)