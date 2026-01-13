import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# ============ 1. 定义工具 ============
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如：北京、上海"
                }
            },
            "required": ["city"]
        }
    }
]

# ============ 2. 工具的实际实现 ============
def get_weather(city: str) -> str:
    """模拟获取天气（实际项目中会调用真实API）"""
    # 这里是模拟数据，实际可以调用天气API
    weather_data = {
        "北京": "晴天，25°C",
        "上海": "多云，28°C",
        "广州": "雷阵雨，30°C"
    }
    return weather_data.get(city, f"未找到{city}的天气信息")

# ============ 3. 执行工具的函数 ============
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """根据工具名称执行对应的函数"""
    if tool_name == "get_weather":
        return get_weather(tool_input["city"])
    return "未知工具"

# ============ 4. 调用 Claude（带工具） ============
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,  # 告诉 Claude 有哪些工具可用
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ]
)

# ============ 5. 查看 Claude 的响应 ============
print("Claude 的响应类型:", response.stop_reason)
print("Claude 的响应内容:")
for block in response.content:
    print(f"  - 类型: {block.type}")
    if block.type == "tool_use":
        print(f"    工具名: {block.name}")
        print(f"    参数: {block.input}")
        print(f"    工具ID: {block.id}")
        
        # 执行工具
        result = execute_tool(block.name, block.input)
        print(f"    执行结果: {result}")
    elif block.type == "text":
        print(f"    文本: {block.text}")
