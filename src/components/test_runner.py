from browser_use import Agent
from components.agent import on_step_end_hook

async def test_single_scenario(agent: Agent, scenario_name: str) -> dict:
    """测试单个演示场景，返回结果"""
    agent.add_new_task(f'''
    在演示中心列表中，点击"{scenario_name}"场景，等待进入演示页面
    1. 点击"开始演示"
    2. 按照手指图标指示的位置，依次点击每一步
    3. 如果有"下一步"按钮就点击继续
    4. 直到演示结束（无更多引导步骤）
    5. 记录是否成功完成所有步骤
    6. 返回演示中心列表页面
    ''')
    history = await agent.run(on_step_end=on_step_end_hook, max_steps=50)
    
    return {
        'scenario': scenario_name,
        'success': history.is_successful(),
        'errors': [e for e in history.errors() if e],
        'steps': history.number_of_steps(),
        'screenshots': history.screenshot_paths(),
    }