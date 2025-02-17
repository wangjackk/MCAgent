from qtHumanAgent import QtHumanAgent

# 全局变量
human_agent: QtHumanAgent = None


def init_human_agent(name: str, member_id: str) -> QtHumanAgent:
    """初始化全局human_agent"""
    global human_agent
    if human_agent is not None:
        # 如果已经存在实例，只更新必要的属性
        if human_agent.name != name or human_agent.member_id != member_id:
            human_agent.name = name
            human_agent.member_id = member_id
    else:
        # 如果不存在实例，创建新的
        print('init:', name, member_id)
        human_agent = QtHumanAgent(name, member_id)
        human_agent.base_url = 'http://121.37.253.121'
    return human_agent


def get_human_agent() -> QtHumanAgent:
    """获取全局human_agent"""
    return human_agent
