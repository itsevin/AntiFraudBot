<div align="center">


# AntiFraudBot

_亮剑网络诈骗，共筑社区网盾_

<p align="center">
    <!-- GitHub主页 -->
    <a style="margin-inline:5px" target="_blank" href="https://github.com/itsevin/AntiFraudBot">
        <img src="https://img.shields.io/badge/GitHub-Home-blue?style=flat&logo=GitHub" title="Github主页">
    </a>
    <!-- py版本 -->
    <img src="https://img.shields.io/badge/Python-3.9+-blue" alt="python">
    <!-- nonebot版本 -->
    <a style="margin-inline:5px" target="_blank" href="https://github.com/nonebot/nonebot2">
        <img src="https://img.shields.io/badge/Nonebot2-Latest-blue" title="nonebot2">
    </a>
</p>


</div>

## 简介

一款基于 [NoneBot2](https://github.com/nonebot/nonebot2) 和 [OneBot 11](https://onebot.dev/) 的反诈机器人。

## 特色

- 反诈骗宣传
- 聊天内容安全监测
- 兼容性强：Windows和Linux都可以部署

## 功能

- 反诈知识点推送
- 诈骗案例推送
- 关键词检测
- 链接检测

> AT机器人或者输入`帮助`以触发功能菜单

## 部署

### 文件下载

使用Git工具拉取文件：

```bash
git clone https://github.com/itsevin/AntiFraudBot.git
```

或者直接下载源代码并解压

### 依赖下载

1. 安装Python，版本要求 >= 3.9 ，推荐 3.10

2. 下载 poetry 进行依赖管理

   ```bash
   pip install poetry
   ```

3. 下载依赖

   ```bash
   poetry install
   ```

### 配置

打开`.env.prod`，按照注释说明合理填写配置项

#### 链接检测接口说明

参考 [URL风险检测接入指南](https://help.aliyun.com/document_detail/2709155.html)的步骤一、二获取 AccessKey 信息

> 该功能由阿里云支持，按量计费，30元/万次

### 启动

```bash
poetry run nb run
```

## 贡献

如果你有想法、有能力，欢迎:

- [提交 Issue](https://github.com/itsevin/AntiFraudBot/issues)
- [提交 Pull request](https://github.com/itsevin/AntiFraudBot/pulls)

## 声明

此项目仅用于学习交流，请勿用于非法用途。

## 许可证

本项目使用 [MIT](https://github.com/itsevin/AntiFraudBot/blob/main/LICENSE) 作为开源许可证。