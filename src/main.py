import asyncio
from components.agent import (
    create_browser, 
    create_llm, 
    create_tools, 
    get_sensitive_data,
    on_step_end_hook,
    close_browser
)
from components.test_runner import test_single_scenario
from components.reporter import print_test_report
from browser_use import Agent

async def main():
    browser = await create_browser()
    await browser.start()
    
    # 登录
    agent = Agent(
        task='''
        1. 打开 https://xft.cmbchina.com/#/workbench 
        2. 输入账号 login_user 密码 login_pass 登录'
        3. 调用 wait_for_human_login 等待用户扫码登录成功后继续执行后续任务
        ''',
        sensitive_data=get_sensitive_data(),
        browser=browser,
        tools=create_tools(),
        llm=create_llm(),
        use_vision=False,  # 硅基流动的GLM-4模型不支持视觉，必须设为False
    )
    await agent.run(max_steps=4)

    # 扫码进入演示中心
    # agent.add_new_task('''
    # 1. 在演示中心列表页遍历点击每个模块的子场景
    # 2. 进入每个子场景后，点击"开始演示"按钮                   
    # ''')
    # await agent.run(on_step_end=on_step_end_hook)

    # 遍历测试每个场景
    scenarios = [
        '应发工资快捷算税', '集团个税', '集团代发',
        '薪资代发', '数电发票高效合规管理'
    ]
    
    results = []
    for name in scenarios:
        result = await test_single_scenario(agent, name)
        results.append(result)

    # 输出测试报告
    print_test_report(results)
    
    # 注意：不要在这里关闭浏览器，因为可能还有其他任务需要使用
    # 如果确定这是最后一个任务，可以取消下面的注释
    # await browser.kill()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # 程序结束时关闭浏览器
        close_browser()