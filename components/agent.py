import asyncio, base64, datetime
from pathlib import Path
from browser_use import Agent, Browser, ActionResult, ChatOpenAI, BrowserSession, Controller
from browser_use.browser.events import ScreenshotEvent
from dotenv import load_dotenv
import os


load_dotenv()  # 加载环境变量

SCREENSHOT_DIR = Path('./demo_test_screenshots')
SCREENSHOT_DIR.mkdir(exist_ok=True)

# 全局浏览器实例，用于复用
_GLOBAL_BROWSER_INSTANCE = None

def create_llm():
    """创建并返回LLM实例"""
    # 使用硅基流动的GLM-4模型
    return ChatOpenAI(
        model='Qwen/Qwen3-VL-32B-Instruct'  # 硅基流动上的正确GLM-4模型名称
    )
    
    # 如果需要使用Browser Use，可以取消注释下面的代码：
    # return ChatBrowserUse()


def create_controller():
    controller = Controller()

    @controller.action(description='等待人工完成扫码登录并切换到新打开的演示中心tab页')
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

    return controller



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
    
    auth_file = 'auth.json'
    
    if not os.path.exists(auth_file):
        print("🆕 首次运行，导出浏览器认证状态")
        browser = Browser.from_system_chrome(
            enable_default_extensions=False,
             channel='msedge',
        )
        await browser.start()
        await browser.export_storage_state(auth_file)
        await browser.stop()
    else:
        print("📦 已存在认证文件，跳过导出")
    
    _GLOBAL_BROWSER_INSTANCE = Browser( channel='msedge', ignore_default_args=['--extensions-on-chrome-urls'], storage_state=auth_file,enable_default_extensions=False)
    return _GLOBAL_BROWSER_INSTANCE

def close_browser():
    """关闭全局浏览器实例"""
    global _GLOBAL_BROWSER_INSTANCE
    if _GLOBAL_BROWSER_INSTANCE is not None:
        asyncio.run(_GLOBAL_BROWSER_INSTANCE.kill())
        _GLOBAL_BROWSER_INSTANCE = None
        print("🧹 浏览器实例已关闭")