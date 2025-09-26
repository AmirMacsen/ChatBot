import asyncio
import json
import aiohttp

url = "http://localhost:7861/chat/chat"
headers = {
    "Content-Type": "application/json"
}

data = {
  "query": "你是谁",
  "conversation_id": "",
  "history_len": -1,
  "history": [
  ],
  "stream": False,
  "model_name": "DeepSeek-R1-Distill-Qwen-1.5B",
  "temperature": 0.7,
  "max_tokens": 512,
  "prompt_name": "default"
}

async def main():
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Sending request to {url}")
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=300)) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {response.headers}")
                print(f"Content-Type: {response.content_type}")
                
                if response.status == 200:
                    print("Starting to read response...")
                    # 读取所有数据
                    content = await response.read()
                    print(f"Raw content length: {len(content)}")
                    print(f"Raw content: {content.decode('utf-8')}")
                    
                    # 或者逐行读取
                    # async for line in response.content:
                    #     if line:
                    #         decoded_line = line.decode('utf-8')
                    #         print(f"Raw line: {repr(decoded_line)}")
                    #         if decoded_line.startswith('data: '):
                    #             # 解析 SSE 数据
                    #             json_data = decoded_line[6:]  # 移除 'data: ' 前缀
                    #             if json_data.strip() != '[DONE]':
                    #                 try:
                    #                     parsed_data = json.loads(json_data)
                    #                     print(f"Received: {parsed_data}")
                    #                 except json.JSONDecodeError:
                    #                     print(f"Raw data: {json_data}")
                    #         else:
                    #             print(f"Non-SSE line: {decoded_line}")
                    #     else:
                    #         print("Empty line received")
                else:
                    # 处理错误响应
                    error_text = await response.text()
                    print(f"Error {response.status}: {error_text}")
        except asyncio.TimeoutError:
            print("Request timed out")
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())