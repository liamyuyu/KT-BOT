"""
使用 Playwright 测试对话功能并捕获网络请求
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_chat():
    print("=== 启动 Playwright 测试 ===\n")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 捕获所有网络请求
        requests_data = []
        
        async def handle_request(request):
            if 'chat' in request.url:
                try:
                    post_data = request.post_data
                    if post_data:
                        requests_data.append({
                            'url': request.url,
                            'method': request.method,
                            'data': json.loads(post_data) if post_data else None
                        })
                        print(f"\n📤 捕获到对话请求:")
                        print(f"URL: {request.url}")
                        print(f"方法: {request.method}")
                        print(f"数据:\n{json.dumps(json.loads(post_data), indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"解析请求失败: {e}")
        
        async def handle_response(response):
            if 'chat' in response.url and response.status == 422:
                print(f"\n❌ 收到 422 响应:")
                print(f"URL: {response.url}")
                try:
                    body = await response.json()
                    print(f"错误详情:\n{json.dumps(body, indent=2, ensure_ascii=False)}")
                except:
                    print(f"响应文本: {await response.text()}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        # 访问应用
        print("📱 打开应用: http://localhost:7861")
        await page.goto('http://localhost:7861', wait_until='load')
        
        # 等待页面加载
        print("⏳ 等待页面加载...")
        await asyncio.sleep(5)

        # 尝试查找输入框并发送消息
        print("\n🔍 查找输入框...")
        try:
            # 查找 Gradio 的 textarea
            print("等待输入框出现并可用...")

            # 等待 textarea 出现
            input_box = await page.wait_for_selector('textarea', timeout=10000)
            print("✅ 找到输入框")

            # 等待输入框变为可用（enabled）
            print("⏳ 等待输入框启用...")
            max_retries = 30
            for i in range(max_retries):
                is_disabled = await input_box.is_disabled()
                if not is_disabled:
                    print(f"✅ 输入框已启用 (尝试 {i+1}/{max_retries})")
                    break
                await asyncio.sleep(1)
            else:
                print(f"⚠️ 输入框仍然禁用，但继续尝试...")

            # 尝试输入消息
            print("\n✍️ 输入测试消息: '你好，请介绍一下自己'")
            await input_box.click()
            await asyncio.sleep(0.5)
            await input_box.fill("你好，请介绍一下自己")
            await asyncio.sleep(1)
            print("✅ 消息已输入")

            # 查找并点击发送按钮
            print("\n🔍 查找发送按钮...")

            # Gradio 通常使用 button 标签
            buttons = await page.query_selector_all('button')
            print(f"找到 {len(buttons)} 个按钮")

            # 尝试找到发送按钮（通常在输入框附近）
            send_button = None
            for button in buttons:
                try:
                    # 检查按钮是否可见
                    is_visible = await button.is_visible()
                    if is_visible:
                        # 尝试获取按钮文本或属性
                        text_content = await button.text_content()
                        if text_content:
                            print(f"  按钮文本: '{text_content.strip()}'")
                except:
                    pass

            # 尝试通过回车发送
            print("\n⌨️  尝试按回车键发送消息...")
            await input_box.press('Enter')
            print("✅ 已按下回车键")

            # 等待响应
            print("\n⏳ 等待 AI 响应（最多 20 秒）...")
            await asyncio.sleep(20)

            # 检查是否有响应
            print("\n🔍 检查页面内容...")
            page_content = await page.content()
            if "你好" in page_content or "很高兴" in page_content or "帮助" in page_content:
                print("✅ 检测到 AI 响应！")
            else:
                print("⚠️ 未检测到明确的 AI 响应")

        except Exception as e:
            print(f"❌ 操作失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 保持浏览器打开一会儿以便观察
        print("\n⏳ 保持浏览器打开 10 秒以便观察...")
        await asyncio.sleep(10)
        
        await browser.close()
        
        print("\n=== 测试完成 ===")
        if requests_data:
            print(f"\n📊 共捕获 {len(requests_data)} 个对话请求")

if __name__ == "__main__":
    asyncio.run(test_chat())
