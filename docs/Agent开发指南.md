# 接口自动化 Agent 开发指南

> 面向测试同事的入门文档，帮助你理解和使用 `api_test_agent.py`

---

## 一、什么是 Agent？

### 1.1 一句话解释

**Agent = AI + 工具 + 循环**

- **AI**：Claude（大语言模型），负责"想"
- **工具**：Python 函数，负责"做"
- **循环**：不断重复"想→做→看结果→再想"

### 1.2 和普通 AI 的区别

| 普通 AI（ChatGPT） | Agent |
|-------------------|-------|
| 你问：怎么测试这个接口？ | 你说：帮我测试这个接口 |
| 它答：你可以这样这样... | 它做：读文档→写代码→执行→返回结果 |
| **只动嘴** | **动手干活** |

### 1.3 和自动化脚本的区别

| 自动化脚本 | Agent |
|-----------|-------|
| 流程写死在代码里 | AI 实时决定下一步 |
| 遇到意外就报错 | 遇到意外自己想办法 |
| 改需求要改代码 | 改需求只需改指令 |

**举例：**
```
自动化脚本：读取→生成→执行（固定三步，中间出错就挂了）

Agent：读取→生成→执行→失败了→看看什么错→调试一下→
       重新生成→再执行→还是不行→换个方案→成功了
```

---

## 二、api_test_agent.py 代码结构

整个文件约 200 行，分为 5 个部分：

```
api_test_agent.py
│
├── 1. 工具定义（tools）        # 告诉 AI 有哪些工具可用
│
├── 2. 工具实现（functions）    # 工具的真正代码
│
├── 3. 工具执行器（execute_tool）# 根据名字调用对应函数
│
├── 4. System Prompt            # 给 AI 的指导方针
│
└── 5. Agent 主循环（run_agent） # 核心：循环调用 AI
```

### 2.1 工具定义

```python
tools = [
    {
        "name": "read_swagger",           # 工具名
        "description": "读取 Swagger 文档", # 告诉 AI 这个工具干嘛的
        "input_schema": {                  # 参数格式
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"}
            }
        }
    },
    ...
]
```

**现有工具：**

| 工具名 | 功能 |
|--------|------|
| `read_swagger` | 读取 Swagger/OpenAPI 文档 |
| `write_test_file` | 把测试代码写入 tests/ 目录 |
| `run_pytest` | 执行 pytest 测试 |
| `read_file` | 读取任意文件 |
| `send_http_request` | 发送 HTTP 请求 |
| `list_files` | 列出目录文件 |

### 2.2 工具实现

每个工具对应一个 Python 函数：

```python
def read_swagger(file_path: str) -> str:
    """读取 Swagger 文档"""
    with open(file_path, 'r') as f:
        return f.read()

def write_test_file(file_name: str, content: str) -> str:
    """写入测试文件"""
    with open(f"tests/{file_name}", 'w') as f:
        f.write(content)
    return "写入成功"

def run_pytest(test_file: str = None) -> str:
    """运行 pytest"""
    result = subprocess.run(["pytest", test_file], capture_output=True)
    return result.stdout
```

### 2.3 工具执行器

根据工具名调用对应函数：

```python
def execute_tool(name: str, input_data: dict) -> str:
    if name == "read_swagger":
        return read_swagger(input_data["file_path"])
    elif name == "write_test_file":
        return write_test_file(input_data["file_name"], input_data["content"])
    elif name == "run_pytest":
        return run_pytest(input_data.get("test_file"))
    ...
```

### 2.4 System Prompt

给 AI 的"角色设定"和"工作指南"：

```python
SYSTEM_PROMPT = """你是一个专业的接口自动化测试 Agent。

你的任务是：
1. 读取 Swagger 文档，理解接口定义
2. 为每个接口生成 pytest 测试用例
3. 运行测试并分析结果
4. 如果测试失败，分析原因并修复代码

生成测试代码时请遵循以下规范：
- 使用 pytest 框架
- 使用 requests 库发送请求
- 添加清晰的中文注释
...
"""
```

> **注意：** 这是建议，不是强制。AI 可能根据实际情况调整步骤。

### 2.5 Agent 主循环（核心）

```python
def run_agent(user_message: str):
    # 初始化对话
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        # 1. 调用 Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )
        
        # 2. 如果 AI 说"我做完了"，结束循环
        if response.stop_reason == "end_turn":
            print(response.content)
            break
        
        # 3. 如果 AI 要调用工具
        for block in response.content:
            if block.type == "tool_use":
                # 执行工具
                result = execute_tool(block.name, block.input)
                # 把结果告诉 AI
                messages.append(tool_result)
        
        # 4. 继续下一轮循环...
```

**流程图：**

```
用户指令
    ↓
┌─────────────────────────────┐
│  调用 Claude API            │
│  "你觉得下一步该做什么？"    │
└─────────────┬───────────────┘
              ↓
        ┌─────┴─────┐
        │ AI 返回    │
        └─────┬─────┘
              ↓
     ┌────────┴────────┐
     │                 │
  tool_use          end_turn
  (要用工具)        (做完了)
     │                 │
     ↓                 ↓
  执行工具           结束
     │
     ↓
  结果发回给 AI
     │
     ↓
  继续循环 ←─────────┘
```

---

## 三、如何使用

### 3.1 环境准备

```bash
# 1. 安装依赖
pip install anthropic python-dotenv requests pytest

# 2. 配置 API Key（编辑 .env 文件）
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 3.2 运行 Agent

**交互模式：**
```bash
python api_test_agent.py
```

然后输入指令：
```
👤 请输入指令: 读取 swagger/petstore.json，为所有接口生成测试用例
```

**代码调用：**
```python
from api_test_agent import run_agent

run_agent("读取 swagger/petstore.json，生成测试用例")
```

### 3.3 常用指令

| 指令 | 说明 |
|------|------|
| 读取 swagger/xxx.json，生成测试用例 | 从 Swagger 生成 pytest 代码 |
| 运行测试 | 执行 pytest |
| 运行测试，如果失败就修复 | 执行 + 自动修复 |
| 读取 tests/test_xxx.py，分析代码 | 查看和分析测试文件 |
| 列出 tests 目录的文件 | 查看已有测试 |

---

## 四、如何扩展（添加新工具）

### 4.1 三步添加新工具

**例子：添加一个"发送钉钉通知"工具**

**第一步：定义工具**（在 tools 列表中添加）

```python
{
    "name": "send_dingtalk",
    "description": "发送钉钉机器人通知",
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "通知内容"
            }
        },
        "required": ["message"]
    }
}
```

**第二步：实现工具**（写一个函数）

```python
def send_dingtalk(message: str) -> str:
    """发送钉钉通知"""
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    data = {"msgtype": "text", "text": {"content": message}}
    response = requests.post(webhook, json=data)
    return "发送成功" if response.ok else "发送失败"
```

**第三步：注册工具**（在 execute_tool 中添加）

```python
def execute_tool(name: str, input_data: dict) -> str:
    ...
    elif name == "send_dingtalk":
        return send_dingtalk(input_data["message"])
```

**然后就可以这样用了：**
```
👤 请输入指令: 运行测试，完成后发钉钉通知告诉我结果
```

### 4.2 常见扩展场景

| 需求 | 添加的工具 |
|------|-----------|
| 测试完发通知 | send_dingtalk, send_email |
| 操作数据库 | query_mysql, insert_data |
| 需要登录 | login, get_token |
| 操作 Git | git_add, git_commit |
| 生成报告 | generate_html_report |

---

## 五、工作原理图解

### 5.1 一次完整的执行过程

```
你: "读取 swagger/petstore.json，生成测试用例，运行测试"
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 第1轮                                                        │
│                                                              │
│ Claude 思考: "用户要我读 Swagger，我先用 read_swagger 工具"   │
│ Claude 返回: tool_use: read_swagger("swagger/petstore.json") │
│                          │                                   │
│ 你的代码执行工具，返回 Swagger 内容                           │
│                          │                                   │
│ 内容发回给 Claude                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 第2轮                                                        │
│                                                              │
│ Claude 思考: "我看到有4个接口，现在生成测试代码"              │
│ Claude 返回: tool_use: write_test_file("test_pet.py", "...")  │
│                          │                                   │
│ 你的代码执行工具，文件写入成功                                │
│                          │                                   │
│ "写入成功" 发回给 Claude                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 第3轮                                                        │
│                                                              │
│ Claude 思考: "代码写好了，运行测试看看"                       │
│ Claude 返回: tool_use: run_pytest("test_pet.py")              │
│                          │                                   │
│ 你的代码执行 pytest，返回测试结果                             │
│                          │                                   │
│ 测试结果发回给 Claude                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 第4轮                                                        │
│                                                              │
│ Claude 思考: "测试全部通过，任务完成"                         │
│ Claude 返回: end_turn + "已完成，共生成20个测试用例，全部通过" │
│                          │                                   │
│ 循环结束                                                     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 遇到错误时的自动修复

```
第3轮: 运行测试 → 3个用例失败
                    │
                    ▼
第4轮: Claude 自己决定 → "看看失败原因"
       调用 read_file 查看错误详情
                    │
                    ▼
第5轮: Claude 分析 → "原来是断言写错了"
       调用 write_test_file 修复代码
                    │
                    ▼
第6轮: Claude → "再跑一次测试"
       调用 run_pytest
                    │
                    ▼
第7轮: 全部通过 → 结束
```

**这就是 Agent 的智能之处：不需要你写"如果失败就修复"的代码，AI 自己会判断。**

---

## 六、常见问题

### Q1: API Key 从哪里获取？

访问 https://console.anthropic.com/ 注册并创建 API Key。

### Q2: 费用怎么算？

按 token 计费，大约 $3/百万输入 token，$15/百万输出 token。跑一次测试生成大概几毛钱。

### Q3: 可以用其他模型吗？

可以，把 `claude-sonnet-4-20250514` 换成其他模型：
- `claude-opus-4-20250514`：更聪明，更贵
- `claude-haiku-3-5-20241022`：更快，更便宜

也可以改成 OpenAI 的 API，逻辑类似。

### Q4: Agent 会不会乱搞？

工具是你定义的，Agent 只能调用你给的工具。它想删数据库也删不了——除非你给它删数据库的工具。

### Q5: 怎么调试 Agent？

运行时会打印每一轮的思考和工具调用，可以看到完整过程。如果行为不对，调整 System Prompt。

---

## 七、总结

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Agent = AI（Claude） + 工具（Python函数） + 循环           │
│                                                             │
│   你要做的：                                                 │
│   1. 定义工具（告诉 AI 有什么能力）                          │
│   2. 实现工具（写 Python 函数）                              │
│   3. 给指令（告诉 AI 你要什么）                              │
│                                                             │
│   AI 来做的：                                                │
│   1. 理解你的指令                                            │
│   2. 决定用什么工具、什么顺序                                │
│   3. 根据结果调整策略                                        │
│   4. 直到完成任务                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心文件就一个：`api_test_agent.py`，约 200 行代码。**

想加功能？加工具。
想改行为？改 Prompt。
就这么简单。
