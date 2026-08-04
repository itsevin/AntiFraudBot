# 📦 Content, data, and third-party notice

The [MIT License](LICENSE) applies to project code authored for AntiFraudBot unless a file states otherwise.

## Bundled educational content

The `source/` directory currently includes anti-fraud images, case-study text, keywords, and quiz questions. The original files do not contain a complete machine-readable provenance manifest. Therefore:

- do not assume that every bundled content item can be relicensed under MIT;
- review the material before redistribution or commercial use;
- remove or replace any item whose source or permission cannot be established;
- contributors adding content must state its source and redistribution basis;
- personal information, account identifiers, phone numbers, QR codes, and private case details must be removed.

The content is provided for anti-fraud education and demonstration. It is not legal advice, an official fraud database, or a guarantee that a message is safe or fraudulent.

## Third-party services

Optional integrations may send configured input to external providers, including an OpenAI-compatible model API and Alibaba Cloud content-safety services. Operators are responsible for:

- reviewing provider terms, pricing, retention, and regional requirements;
- minimizing personal or confidential data sent to providers;
- configuring credentials with the least privileges required;
- rotating credentials if accidental disclosure is suspected.

## Trademarks and platforms

QQ, OneBot implementations, NoneBot2, Alibaba Cloud, model providers, and other product names belong to their respective owners. Their mention does not imply endorsement.

---

# 📦 内容、数据与第三方声明

[MIT License](LICENSE) 默认适用于 AntiFraudBot 项目自行编写的代码，文件另有声明的除外。

`source/` 目录包含反诈知识图片、案例文本、关键词和题库。现有文件没有完整的机器可读来源清单，因此：

- 不应默认认为所有素材都可以按 MIT 再许可；
- 再分发或商业使用前应逐项确认来源与授权；
- 无法确认来源或许可的素材应删除或替换；
- 新增内容的贡献者必须说明来源和再分发依据；
- 必须移除个人信息、账号标识、电话号码、二维码和具体案件隐私。

这些内容只用于反诈教育和功能演示，不构成法律意见、官方诈骗数据库或对消息安全性的保证。

可选集成可能把配置的输入发送给兼容 OpenAI API 的模型服务或阿里云内容安全服务。部署者需要自行审核服务条款、计费、数据保留、地域要求和最小权限配置。
