# test_scenarios.py
import asyncio, datetime
from pathlib import Path
from browser_use import Agent
from components.agent import (
    create_browser, create_llm, create_tools,
    on_step_end_hook, close_browser,
    SCREENSHOT_DIR, REPORT_PATH
)


async def test_single_scenario(browser, scenario_url: str) -> dict:
    agent = Agent(
        task=f'''
            打开 {scenario_url} 页面，等待5秒让页面完全加载
            1. 点击“开始演示”图片按钮，该按钮可以使用div[class*="DemoMap_startBtn"]获取到，进入演示场景步骤指引状态
            2. 查看是否页面是否有提示“收起演示地图”弹窗提示，点击“收起演示地图”按钮，如果页面还有“开始演示”按钮则代表带第一步执行失败，继续执行第一步
            3. 准确找到指引手指图标指向的元素截屏并点击该元素，没有则点击工具栏的“指引气泡”按钮唤起指引手指图标
            4. 如果点击唤起指引后没有出现指引手指，截取当前屏幕结束任务。否则继续点击指引气泡选中的元素，直到页面没有指引手指出现，代表完成了整个演示场景的测试
            5. 将测试结果写在D:\FILE\程序员的自我修养\my-browser-use\src\demo_test_screenshots目录中
        ''',
        browser=browser,
        tools=create_tools(),
        llm=create_llm(),
        use_vision=True,
        max_failures=6,
    )
    history = await agent.run(on_step_end=on_step_end_hook, max_steps=100)

    return {
        'scenario': scenario_url,
        'success': history.is_successful(),
        'errors': [str(e) for e in history.errors() if e],
        'steps': history.number_of_steps(),
        'screenshots': history.screenshot_paths(),
    }


def generate_report(results: list[dict]):
    """生成 Markdown 测试报告到项目目录"""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed

    lines = [
        f'# 演示中心自动化测试报告',
        f'',
        f'> 生成时间: {now}',
        f'',
        f'## 概览',
        f'',
        f'| 指标 | 数值 |',
        f'|------|------|',
        f'| 总场景数 | {total} |',
        f'| ✅ 通过 | {passed} |',
        f'| ❌ 失败 | {failed} |',
        f'| 通过率 | {passed/total*100:.1f}% |' if total > 0 else '',
        f'',
        f'## 详细结果',
        f'',
    ]

    for i, r in enumerate(results, 1):
        status = '✅ 通过' if r['success'] else '❌ 失败'
        lines.append(f'### 场景 {i}: {status}')
        lines.append(f'')
        lines.append(f'- **URL**: `{r["scenario"][:80]}...`')
        lines.append(f'- **步骤数**: {r["steps"]}')
        lines.append(f'')

        if r['errors']:
            lines.append(f'**错误信息:**')
            lines.append(f'')
            for err in r['errors']:
                lines.append(f'- `{err[:200]}`')
            lines.append(f'')

        # 引用截图（使用相对路径）
        screenshots = [s for s in (r.get('screenshots') or []) if s]
        if screenshots:
            lines.append(f'**截图:**')
            lines.append(f'')
            for s in screenshots:
                # 转为相对于报告文件的路径
                rel_path = Path(s).name
                lines.append(f'![step screenshot](./screenshots/{rel_path})')
            lines.append(f'')

        lines.append(f'---')
        lines.append(f'')

    REPORT_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f'📄 测试报告已生成: {REPORT_PATH}')


async def main():
    scenarios = [
        'https://xft.cmbchina.com/omsapp/#/xft-trail?scenecode=outbound_invoice&xftToken=...',
        # 添加更多场景 URL...
    ]

    browser = await create_browser()
    results = []

    for url in scenarios:
        result = await test_single_scenario(browser, url)
        results.append(result)

    generate_report(results)
    close_browser()


if __name__ == '__main__':
    asyncio.run(main())