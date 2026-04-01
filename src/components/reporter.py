def print_test_report(results):
    """输出测试报告"""
    print('\n' + '='*60)
    print('📊 演示中心自动化测试报告')
    print('='*60)
    for r in results:
        status = '✅ 通过' if r['success'] else '❌ 失败'
        print(f"{status} | {r['scenario']} | 步骤数: {r['steps']}")
        if r['errors']:
            for e in r['errors']:
                print(f"    错误: {e}")
            print(f"    截图: {r['screenshots']}")