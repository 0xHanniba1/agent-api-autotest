import anthropic
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
    },
    {
        "name": "read_file",
        "description": "读取文件内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["file_path"]
        }
    }
]

# ============ 2. 工具实现 ============
def get_weather(city: str) -> str:
    weather_data = {
        "北京": "晴天，25°C",
        "上海": "多云，28°C", 
        "广州": "雷阵雨，30°C"
    }
    return weather_data.get(city, f"未找到{city}的天气信息")

def read_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"

def execute_tool(name: str, input_data: dict) -> str:
    if name == "get_weather":
        return get_weather(input_data["city"])
    elif name == "read_file":
        return read_file(input_data["file_path"])
    return "未知工具"

# ============ 3. Agent 循环 ============
def run_agent(user_message: str):
    print(f"\n{'='*50}")
    print(f"用户: {user_message}")
    print('='*50)
    
    messages = [{"role": "user", "content": user_message}]
    
    turn = 0
    while True:
        turn += 1
        print(f"\n--- 第 {turn} 轮对话 ---")
        
        # 调用 Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        print(f"停止原因: {response.stop_reason}")
        
        # 如果 Claude 不需要调用工具了，结束循环
        if response.stop_reason == "end_turn":
            # 提取最终文本回复
            for block in response.content:
                if block.type == "text":
                    print(f"\nAgent 最终回答: {block.text}")
            break
        
        # 处理 Claude 的响应（可能包含文本和工具调用）
        assistant_content = []
        tool_results = []
        
        for block in response.content:
            if block.type == "text":
                print(f"Claude 思考: {block.text}")
                assistant_content.append({"type": "text", "text": block.text})
            
            elif block.type == "tool_use":
                print(f"Claude 调用工具: {block.name}({block.input})")
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
                # 执行工具
                result = execute_tool(block.name, block.input)
                print(f"工具返回: {result}")
                
                # 记录工具结果
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        
        # 把 Claude 的响应加入消息历史
        messages.append({"role": "assistant", "content": assistant_content})
        
        # 把工具结果加入消息历史
        messages.append({"role": "user", "content": tool_results})
        
        # 安全限制：最多 10 轮
        if turn >= 10:
            print("达到最大轮次，停止")
            break

# ============ 4. 测试 ============
if __name__ == "__main__":
    # 测试1: 简单天气查询
    run_agent("北京和上海今天天气怎么样？")
    
    # 测试2: 读取文件
    run_agent("帮我读取 step1_basic.py 文件的内容，告诉我这个文件是做什么的")
