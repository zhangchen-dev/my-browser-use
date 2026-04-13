# components/agent.py
import asyncio, base64, datetime, json, os, subprocess
from pathlib import Path
from browser_use import Agent, Browser, Tools, ActionResult, ChatOpenAI, BrowserSession
from browser_use.browser.events import ScreenshotEvent
from dotenv import load_dotenv

load_dotenv()

# 项目当前目录
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
SCREENSHOT_DIR = PROJECT_DIR / 'screenshots'
SCREENSHOT_DIR.mkdir(exist_ok=True)
REPORT_PATH = PROJECT_DIR / 'test_report.md'

_GLOBAL_BROWSER_INSTANCE = None


def create_llm():
    """创建并返回LLM实例"""
    # 使用硅基流动的Qwen-VL模型（多模态）
    return ChatOpenAI(
        model='Qwen/Qwen3-VL-32B-Instruct'  # 硅基流动上的正确多模态模型名称
    )
    
    # 如果需要使用Browser Use，可以取消注释下面的代码：
    # return ChatBrowserUse()


def create_tools():
    tools = Tools()

    @tools.action(description='点击页面右下侧的"开始演示"按钮')
    async def click_start_demo(browser_session: BrowserSession) -> ActionResult:
        page = await browser_session.must_get_current_page()
        elements = await page.get_elements_by_css_selector('div[class*="DemoMap_startBtn"]')
        if not elements:
            return ActionResult(extracted_content='未找到"开始演示"按钮')
        await elements[0].click()
        return ActionResult(extracted_content='已成功点击"开始演示"按钮')

    return tools


async def on_step_end_hook(agent: Agent):
    """步骤结束时的钩子函数"""
    errors = agent.history.errors()
    last_error = errors[-1] if errors else None
    if last_error is None:
        return

    if isinstance(last_error, str) and "Invalid API key" in last_error:
        print(f'❌ API密钥错误: {last_error}')
        return

    try:
        # 获取底层 Playwright page 对象
        playwright_page = await agent.browser_session.get_playwright_page()
        if playwright_page:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            step_num = agent.history.number_of_steps()
            filepath = SCREENSHOT_DIR / f'fail_step{step_num}_{timestamp}.png'
            await playwright_page.screenshot(path=str(filepath))
            print(f'❌ 步骤{step_num}出错 | 截图: {filepath}')
        else:
            print(f'❌ 步骤出错，无法获取页面: {last_error}')
    except Exception as e:
        print(f'❌ 截图失败: {e} | 错误详情: {last_error}')
def close_chrome_processes():
    try:
        subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'],
                       capture_output=True, text=True, shell=True)
    except Exception:
        pass


async def create_browser():
    global _GLOBAL_BROWSER_INSTANCE
    if _GLOBAL_BROWSER_INSTANCE is not None:
        return _GLOBAL_BROWSER_INSTANCE

    close_chrome_processes()
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Write-Host $env:LOCALAPPDATA\\Google\\Chrome\\User Data'],
            capture_output=True, text=True, shell=True
        )
        user_data_dir = result.stdout.strip()
        _GLOBAL_BROWSER_INSTANCE = Browser(
            channel='chrome', user_data_dir=user_data_dir,
            enable_default_extensions=False, headless=False,
            window_size=(1440, 1000)
        )
        await _GLOBAL_BROWSER_INSTANCE.start()
    except Exception:
        _GLOBAL_BROWSER_INSTANCE = Browser(
            channel='chrome', enable_default_extensions=False, headless=False
        )
    return _GLOBAL_BROWSER_INSTANCE


def close_browser():
    global _GLOBAL_BROWSER_INSTANCE
    if _GLOBAL_BROWSER_INSTANCE is not None:
        asyncio.run(_GLOBAL_BROWSER_INSTANCE.kill())
        _GLOBAL_BROWSER_INSTANCE = None