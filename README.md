# 🚀 数据标注系统

一个简单好用的数据标注工具，专为处理问答类数据设计，支持数学公式显示。

## ✨ 特色功能

* 📊 支持上传 JSONL 格式数据进行标注
* ⏱️ 自定义倒计时，提高标注效率
* 🧮 完美渲染 LaTeX 数学公式
* 📝 简单直观的"正确/错误"二分类标注
* 📱 响应式设计，适配多种设备
* 🔄 支持导航和导出标注结果

## 🛠️ 技术栈

* **前端** ：HTML、CSS、JavaScript、MathJax
* **后端** ：Flask (Python)
* **数据处理** ：JSON、Markdown

## 📋 使用指南

### 1. 部署系统

```bash
# 克隆项目
git clone https://github.com/ChangWang9/data_annotation.git
cd 数据标注系统

# 安装依赖
pip install flask markdown2

# 启动服务
python app.py
```

系统将在 http://localhost:5000 启动

### 2. 上传数据

* 准备好符合格式的 JSONL 文件（每行是一个 JSON 对象）
* 在首页点击"选择文件"上传
* 文件应包含 `question` 和 `neg_reasoning_paths` 字段

### 3. 标注流程

1. 查看显示的问题和回答内容
2. 使用上/下滑按钮浏览长内容
3. 点击 "Right" 或 "Error" 进行标注
4. 系统自动跳转到下一条数据
5. 标注完成后可下载结果

### 4. 小技巧

* 点击"设置倒计时"可自定义每题的标注时间
* 时间到会自动跳转到下一题，提高效率
* 随时可以点击"导出标注"保存当前进度

## 📁 项目结构

```
数据标注系统/
├── app.py             # 核心应用逻辑
├── static/
│   └── style.css      # 样式文件
├── templates/         # HTML模板
│   ├── index.html     # 首页
│   ├── annotate.html  # 标注页
│   └── complete.html  # 完成页
├── uploads/           # 上传文件目录
├── annotations/       # 标注结果保存目录
└── data_files/        # 处理后的数据文件
```

## 📝 数据格式说明

上传的 JSONL 文件格式示例：

```jsonl
{"question": "问题文本", "neg_reasoning_paths": ["回答文本"]}
```

如果数据中包含 LaTeX 公式，系统会自动处理并渲染。
