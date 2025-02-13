from qtHumanAgent import QtHumanAgent

# 全局变量
human_agent: QtHumanAgent = None


def init_human_agent(name: str, member_id: str) -> QtHumanAgent:
    """初始化全局human_agent"""
    global human_agent
    print('init:', name, member_id)
    human_agent = QtHumanAgent(name, member_id)
    return human_agent


def get_human_agent() -> QtHumanAgent:
    """获取全局human_agent"""
    return human_agent
