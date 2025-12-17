# Memexia

> 让你的想法自己长出新想法

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 这是什么？

你有没有过这种体验——读到一个有趣的概念，突然联想到另一个完全不相关的领域，然后发现它们之间居然有奇妙的联系？

Memexia 就是想把这个过程自动化。

给它一个起点（比如"语言会影响思维方式"），它会：
- 通过 LLM 做逻辑推导，生成关联的概念
- 用向量相似度找到和已有知识的连接
- 把这些东西串成一张不断生长的思维图谱

名字来源于 1945 年 Vannevar Bush 提出的 [Memex](https://en.wikipedia.org/wiki/Memex) 概念——一个基于关联而非分类的知识系统。七十多年后，我们终于有工具来实现类似的东西了。

## 项目状态

🚧 **早期开发中** 🚧

目前还在搭建基础架构，核心功能还没完全跑通。如果你感兴趣，欢迎关注或者一起来折腾。

## 技术栈

- **后端**: Python + FastAPI
- **前端**: Svelte + TypeScript
- **LLM**: 支持 OpenAI API / 本地模型
- **向量数据库**: 待定
- **图可视化**: Three.js

## 快速开始

```bash
# 克隆项目
git clone https://github.com/your-username/Memexia.git
cd Memexia

# 安装依赖（推荐用 pnpm）
pnpm install

# 启动开发服务器
pnpm dev
```

详细的配置说明等项目稳定后会补充。

## 能用来干嘛？

想象中的使用场景：

- **个人知识管理**: 不用手动整理笔记，让系统自己发现知识之间的联系
- **研究辅助**: 丢进一个研究问题，看看它能联想到哪些相关领域
- **写作灵感**: 从一个关键词出发，探索可能的展开方向

## 为什么选 AGPL？

这个项目采用 [GNU AGPLv3](LICENSE) 协议。简单说就是：你可以自由使用和修改，但如果你基于它做了什么改进，也需要开源出来。

我觉得这类工具应该是公共基础设施，不希望它被闭源商业化后反过来限制大家使用。

## 参与贡献

现阶段欢迎任何形式的参与：
- 提 Issue 讨论想法
- 帮忙完善文档
- 贡献代码（先开 Issue 聊聊想做什么）

## 联系方式

有问题或想法可以直接开 Issue，或者通过以下方式找到我：
- GitHub: [@ChenXu233](https://github.com/ChenXu233)

---

*如果这个项目对你有帮助，欢迎点个 Star ⭐*
