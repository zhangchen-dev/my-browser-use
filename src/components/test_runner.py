from browser_use import Agent
from components.agent import on_step_end_hook, create_llm, create_tools

async def test_single_scenario(browser, scenario_url: str) -> dict:
    """每个场景创建独立 Agent，复用同一个 browser"""
    agent = Agent(
        task=f'''
            打开 {scenario_url} 页面，等待5秒让页面完全加载
            1. 调用 click_start_demo 工具点击"开始演示"按钮，不适用视觉识别
            2. 等待2秒观察页面变化，如果没有“开始演示”文案则代表元素查找成功，否则继续执行第1步
            3. 查看是否页面是否有提示“收起演示地图”弹窗提示，点击“收起演示地图”按钮
            4. 调用 get_next_click_element_from_config 工具从sessionStorage中读取演示配置，获取当前步骤需要点击的元素选择器
            5. 根据工具返回的选择器信息，在页面上找到对应的元素并点击
            6. 如果页面到“演示结束”页面则执行第7步,否则继续执行第4步
            7. 直到演示结束，返回演示中心列表页面
        ''',
        browser=browser,
        tools=create_tools(),  # 添加工具支持
        llm=create_llm(),
        use_vision=False,  # 使用精确的sessionStorage配置，禁用视觉识别
    )
    
    history = await agent.run(on_step_end=on_step_end_hook, max_steps=20)
    
    return {
        'scenario': scenario_url,
        'success': history.is_successful(),
        'errors': [e for e in history.errors() if e],
        'steps': history.number_of_steps(),
        'screenshots': history.screenshot_paths(),
    }