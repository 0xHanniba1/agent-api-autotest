"""
接口自动化测试 Agent
功能：读取 Swagger 文档 → 生成 pytest 测试用例 → 执行测试 → 自动修复错误
"""

import anthropic
import json
import subprocess
import os
import requests
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. 定义工具
# ============================================================
tools = [
    {
        "name": "read_swagger",
        "description": "读取 Swagger/OpenAPI 文档，获取接口定义。支持 JSON 和 YAML 格式",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Swagger 文件路径，如 swagger/api.json"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_test_file",
        "description": "将生成的 pytest 测试代码写入文件",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "测试文件名，如 test_users.py"
                },
                "content": {
                    "type": "string",
                    "description": "pytest 测试代码内容"
                }
            },
            "required": ["file_name", "content"]
        }
    },
    {
        "name": "run_pytest",
        "description": "运行 pytest 测试，返回测试结果",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_file": {
                    "type": "string",
                    "description": "要运行的测试文件，如 test_users.py。不填则运行全部测试"
                }
            },
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "读取任意文件内容",
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
    },
    {
        "name": "send_http_request",
        "description": "发送 HTTP 请求测试接口",
        "input_schema": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "HTTP 方法：GET, POST, PUT, DELETE"
                },
                "url": {
                    "type": "string",
                    "description": "完整的请求 URL"
                },
                "headers": {
                    "type": "object",
                    "description": "请求头"
                },
                "body": {
                    "type": "object",
                    "description": "请求体（JSON）"
                }
            },
            "required": ["method", "url"]
        }
    },
    {
        "name": "list_files",
        "description": "列出目录下的文件",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "目录路径，默认为项目根目录"
                }
            },
            "required": []
        }
    }
]

# ============================================================
# 2. 工具实现
# ============================================================

def read_swagger(file_path: str) -> str:
    """读取 Swagger 文档"""
    full_path = os.path.join(PROJECT_DIR, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析 JSON
        if file_path.endswith('.json'):
            data = json.loads(content)
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        # YAML 格式
        elif file_path.endswith(('.yaml', '.yml')):
            import yaml
            data = yaml.safe_load(content)
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        return content
    except FileNotFoundError:
        return f"错误：文件不存在 - {full_path}"
    except Exception as e:
        return f"错误：读取文件失败 - {str(e)}"

def write_test_file(file_name: str, content: str) -> str:
    """写入测试文件"""
    tests_dir = os.path.join(PROJECT_DIR, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    
    file_path = os.path.join(tests_dir, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功：测试文件已写入 - {file_path}"
    except Exception as e:
        return f"错误：写入文件失败 - {str(e)}"

def run_pytest(test_file: str = None) -> str:
    """运行 pytest"""
    tests_dir = os.path.join(PROJECT_DIR, "tests")
    
    if test_file:
        target = os.path.join(tests_dir, test_file)
    else:
        target = tests_dir
    
    try:
        result = subprocess.run(
            ["pytest", target, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=PROJECT_DIR
        )
        output = result.stdout + result.stderr
        return output if output else "测试执行完成，无输出"
    except subprocess.TimeoutExpired:
        return "错误：测试执行超时（60秒）"
    except FileNotFoundError:
        return "错误：pytest 未安装，请运行 pip install pytest"
    except Exception as e:
        return f"错误：执行测试失败 - {str(e)}"

def read_file(file_path: str) -> str:
    """读取文件"""
    full_path = os.path.join(PROJECT_DIR, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"错误：读取文件失败 - {str(e)}"

def send_http_request(method: str, url: str, headers: dict = None, body: dict = None) -> str:
    """发送 HTTP 请求"""
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            json=body,
            timeout=10
        )
        return json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:2000]  # 限制长度
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"错误：请求失败 - {str(e)}"

def list_files(directory: str = None) -> str:
    """列出目录文件"""
    target_dir = os.path.join(PROJECT_DIR, directory) if directory else PROJECT_DIR
    try:
        files = os.listdir(target_dir)
        return "\n".join(files)
    except Exception as e:
        return f"错误：无法列出目录 - {str(e)}"

# ============================================================
# 3. 工具执行器
# ============================================================

def execute_tool(name: str, input_data: dict) -> str:
    """执行工具"""
    if name == "read_swagger":
        return read_swagger(input_data["file_path"])
    elif name == "write_test_file":
        return write_test_file(input_data["file_name"], input_data["content"])
    elif name == "run_pytest":
        return run_pytest(input_data.get("test_file"))
    elif name == "read_file":
        return read_file(input_data["file_path"])
    elif name == "send_http_request":
        return send_http_request(
            input_data["method"],
            input_data["url"],
            input_data.get("headers"),
            input_data.get("body")
        )
    elif name == "list_files":
        return list_files(input_data.get("directory"))
    return "未知工具"

# ============================================================
# 4. Agent 主循环
# ============================================================

SYSTEM_PROMPT = """你是一个专业的接口自动化测试 Agent。你的任务是：

1. 读取 Swagger/OpenAPI 文档，理解接口定义
2. 为每个接口生成 pytest 测试用例
3. 运行测试并分析结果
4. 如果测试失败，分析原因并修复代码

生成测试代码时请遵循以下规范：
- 使用 pytest 框架
- 使用 requests 库发送请求
- 每个接口至少包含：正常请求测试、参数校验测试
- 测试函数命名：test_<接口名>_<场景>
- 添加清晰的中文注释
- 使用 assert 进行断言

文件结构：
- swagger/ 目录存放 Swagger 文档
- tests/ 目录存放测试代码
"""

def run_agent(user_message: str, max_turns: int = 15):
    """运行 Agent"""
    print(f"\n{'='*60}")
    print(f"用户指令: {user_message}")
    print('='*60)
    
    messages = [{"role": "user", "content": user_message}]
    
    turn = 0
    while turn < max_turns:
        turn += 1
        print(f"\n--- 第 {turn} 轮 ---")
        
        # 调用 Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )
        
        print(f"状态: {response.stop_reason}")
        
        # 结束
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"\n🤖 Agent 回复:\n{block.text}")
            break
        
        # 处理响应
        assistant_content = []
        tool_results = []
        
        for block in response.content:
            if block.type == "text":
                print(f"💭 思考: {block.text[:200]}..." if len(block.text) > 200 else f"💭 思考: {block.text}")
                assistant_content.append({"type": "text", "text": block.text})
            
            elif block.type == "tool_use":
                print(f"🔧 调用工具: {block.name}")
                print(f"   参数: {json.dumps(block.input, ensure_ascii=False)[:200]}...")
                
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
                # 执行工具
                result = execute_tool(block.name, block.input)
                result_preview = result[:300] + "..." if len(result) > 300 else result
                print(f"   结果: {result_preview}")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        
        # 更新消息历史
        messages.append({"role": "assistant", "content": assistant_content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
    
    if turn >= max_turns:
        print(f"\n⚠️ 达到最大轮次 ({max_turns})，停止执行")
    
    return messages

# ============================================================
# 5. 主程序入口
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 接口自动化测试 Agent")
    print("="*60)
    print("\n可用指令示例：")
    print("1. 读取 swagger/petstore.json，为所有接口生成测试用例")
    print("2. 运行测试并修复失败的用例")
    print("3. 列出当前的测试文件")
    print("\n输入 'quit' 退出\n")
    
    while True:
        try:
            user_input = input("👤 请输入指令: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            if not user_input:
                continue
            run_agent(user_input)
        except KeyboardInterrupt:
            print("\n再见！")
            break
