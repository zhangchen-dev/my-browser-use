from browser_use import Agent
from components.agent import on_step_end_hook, create_llm

async def test_single_scenario(browser, scenario_url: str) -> dict:
    """每个场景创建独立 Agent，复用同一个 browser"""
    agent = Agent(
        task=f'''
            打开 {scenario_url} 页面，等待5秒让页面完全加载
            1. 找到并点击"开始演示"按钮[class^="DemoMap_startBtn"]
            2. 等待2秒观察页面变化
            3. 查看是否页面是否有提示“收起演示地图”弹窗提示，点击“收起演示地图”按钮
            4. 在页面查找手指元素class="tour-guide-point"，鼠标点击此元素，等待2秒观察页面变化
            5. 如果页面到“演示结束”页面则执行第6步,否则继续执行第4步
            6. 直到演示结束，返回演示中心列表页面
        ''',
        browser=browser,
        llm=create_llm(),
        use_vision=True,
    )
    
    history = await agent.run(on_step_end=on_step_end_hook, max_steps=20)
    
    return {
        'scenario': scenario_url,
        'success': history.is_successful(),
        'errors': [e for e in history.errors() if e],
        'steps': history.number_of_steps(),
        'screenshots': history.screenshot_paths(),
    }