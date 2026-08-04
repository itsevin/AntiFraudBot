# 🎮 User guide

[Documentation](README.md) · [简体中文](../使用指南.md) · [Installation](installation.md)

## Roles

| Role | Capabilities |
|---|---|
| Regular user | Help, check-in, quiz, scores, AI analysis, assistant |
| Group admin or owner | User capabilities plus group feature switches |
| NoneBot superuser | Administrative commands and maintenance |
| Web administrator | Secured dashboard and management APIs |

## Common commands

The effective prefix is controlled by `COMMAND_START`. With the default configuration:

```text
帮助
鉴诈 suspicious text
反诈咨询 question
签到
反诈答题
我的积分
积分排行
开启 关键词检测
关闭 关键词检测
查看配置
```

## Detection behavior

Keyword detection reads active records from the database, warns on matches, and records detection logs. Rules can produce false positives, so group administrators should review the keyword set for their actual context.

URL checks are optional and may send URLs to Alibaba Cloud. They can incur costs and remain subject to provider terms and regional data rules.

## AI analysis

`鉴诈` sends the supplied text to the configured OpenAI-compatible model service. Do not include verification codes, passwords, identity numbers, payment-card data, or complete private conversations. Model output is advisory and may be wrong.

The conversational assistant supports short multi-turn context and lightweight retrieval. OCR for bundled knowledge images is not currently implemented.

## Quiz and scores

`签到` awards the daily check-in score once. `反诈答题` starts a multiple-choice session using questions imported from `source/quiz_bank.json`. Reply with `A`, `B`, `C`, or `D`. `我的积分` and `积分排行` show personal and group-level statistics.

## Scheduled education

Knowledge images and case text come from `source/knowledge/` and `source/example/`. Operators should review content rights, group rules, and posting frequency before enabling scheduled distribution.

## Dashboard

Open `http://127.0.0.1:8000/#/login`. The username is `admin`; the password has no usable default and must be configured by the operator.

The dashboard shows risk metrics, category distribution, AI summaries, a report, and a virtual map. Map positions are deterministic hashes of group identifiers, not real locations. The forecast curve is a heuristic display, not a trained predictive model.

Every business API requires a JWT. An expired or invalid token removes the local session and returns the user to the login page.

## Privacy

The local database may contain QQ user and group identifiers, matched message text, AI inputs and outputs, conversation context, and quiz records. Operators must disclose the bot's behavior, restrict file access, define retention, sanitize exports, and comply with applicable privacy requirements.
