import asyncio, base64, datetime
from pathlib import Path
from browser_use import Agent, Browser, Tools, ActionResult, ChatOpenAI,BrowserSession
from browser_use.browser.events import ScreenshotEvent
from dotenv import load_dotenv
import os
import subprocess


load_dotenv()  # 加载环境变量

SCREENSHOT_DIR = Path('./demo_test_screenshots')
SCREENSHOT_DIR.mkdir(exist_ok=True)

# 全局浏览器实例，用于复用
_GLOBAL_BROWSER_INSTANCE = None

def close_chrome_processes():
    """关闭所有 Chrome 进程，避免端口和文件锁定冲突"""
    try:
        subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                      capture_output=True, text=True, shell=True)
        print("⏹️  已关闭所有 Chrome 进程")
    except Exception as e:
        print(f"ℹ️  关闭 Chrome 进程时出现警告: {e}")

def create_llm():
    """创建并返回LLM实例"""
    # 使用硅基流动的GLM-4模型
    return ChatOpenAI(
        model='zai-org/GLM-4.6'  # 硅基流动上的正确GLM-4模型名称
    )
    
    # 如果需要使用Browser Use，可以取消注释下面的代码：
    # return ChatBrowserUse()


def create_tools():
    tools = Tools()

    @tools.action(description='等待人工完成扫码登录并切换到新打开的演示中心tab页')
    async def wait_for_human_login(browser_session: BrowserSession) -> ActionResult:
        input('\n⏸️ 请手动完成扫码登录并打开演示中心列表页，完成后按回车继续...')
        
        # 获取浏览器上下文中所有 tab 页，切换到最新的 tab
        context = await browser_session.get_browser_context()
        pages = context.pages
        if pages:
            latest_page = pages[-1]  # 最新打开的 tab
            await latest_page.bring_to_front()
            current_url = latest_page.url
        else:
            current_url = 'unknown'

        return ActionResult(
            extracted_content=f'已切换到演示中心列表页，当前URL: {current_url}，请在此页面继续执行任务'
        )

    return tools



async def on_step_end_hook(agent: Agent):
    """步骤结束时的钩子函数，用于错误处理和截图"""
    errors = agent.history.errors()
    last_error = errors[-1] if errors else None
    if last_error is not None:
        # 检查错误是否是字符串类型（如API密钥错误）
        if isinstance(last_error, str) and "Invalid API key" in last_error:
            print(f'❌ API密钥错误: {last_error}')
            return
            
        # 尝试获取截图，但要处理可能的异常
        try:
            screenshot_event = agent.browser_session.event_bus.dispatch(
                ScreenshotEvent(full_page=False)
            )
            await screenshot_event
            result = await screenshot_event.event_result(raise_if_any=True, raise_if_none=True)
            
            # 确保result有screenshot属性
            if hasattr(result, 'screenshot') and result.screenshot:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                step_num = agent.history.number_of_steps()
                url = await agent.browser_session.get_current_page_url()
                filepath = SCREENSHOT_DIR / f'fail_step{step_num}_{timestamp}.png'
                filepath.write_bytes(base64.b64decode(result.screenshot))
                print(f'❌ 步骤{step_num}出错 | URL: {url} | 截图: {filepath}')
            else:
                print(f'❌ 步骤出错但无法获取截图: {last_error}')
        except Exception as e:
            print(f'❌ 截图失败: {e} | 错误详情: {last_error}')

def get_sensitive_data():
    """获取敏感数据"""
    return {
        'login_user': '19891450778',
        'login_pass': '@Zjq123zjq',
    }




async def create_browser():
    """创建并返回浏览器实例，支持复用已存在的实例"""
    global _GLOBAL_BROWSER_INSTANCE
    
    if _GLOBAL_BROWSER_INSTANCE is not None:
        print("🔄 复用已存在的浏览器实例")
        return _GLOBAL_BROWSER_INSTANCE
    
    # 关闭现有 Chrome 进程以避免冲突
    close_chrome_processes()
    
    # 直接使用系统 Chrome 的用户数据目录
    try:
        # 获取 Chrome 用户数据目录路径
        result = subprocess.run(['powershell', '-Command', 'Write-Host $env:LOCALAPPDATA\\Google\\Chrome\\User Data'], 
                              capture_output=True, text=True, shell=True)
        user_data_dir = result.stdout.strip()
        print(f"📁 使用 Chrome 用户数据目录: {user_data_dir}")
        
        _GLOBAL_BROWSER_INSTANCE = Browser(
            channel='chrome',
            user_data_dir=user_data_dir,
            enable_default_extensions=False,
            headless=False  # 确保显示浏览器窗口
        )
        await _GLOBAL_BROWSER_INSTANCE.start()
        print("✅ 浏览器启动成功，使用完整的用户配置")
    except Exception as e:
        print(f"⚠️ 无法使用用户数据目录，回退到基本配置: {e}")
        # 回退方案
        _GLOBAL_BROWSER_INSTANCE = Browser(
            channel='chrome',
            enable_default_extensions=False,
            headless=False
        )
    
    return _GLOBAL_BROWSER_INSTANCE

def close_browser():
    """关闭全局浏览器实例"""
    global _GLOBAL_BROWSER_INSTANCE
    if _GLOBAL_BROWSER_INSTANCE is not None:
        asyncio.run(_GLOBAL_BROWSER_INSTANCE.kill())
        _GLOBAL_BROWSER_INSTANCE = None
        print("🧹 浏览器实例已关闭")
    
