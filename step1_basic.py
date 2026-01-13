import anthropic
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

# 创建客户端（自动读取 ANTHROPIC_API_KEY 环境变量）
client = anthropic.Anthropic()

# 最简单的调用
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "你好，请用一句话介绍什么是Agent"}
    ]
)

# 打印回复
print(response.content[0].text)
