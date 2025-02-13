import sys
import os

# 获取原始模块所在的目录路径
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../client'))
sys.path.append(module_path)

from base import Villager, Werewolf, Prophet, Witch
from hosts import GameHost

styles = [
    "说话风格幽默，喜欢以'天哪！'开头",
    '是个逗逼，总能把严肃的问题讲得像脱口秀一样有趣',
    '一个文艺中二青年，总是沉浸在自己的诗歌和幻想中，觉得自己是下一个莎士比亚',
    '狂傲不羁，说话非常嚣张，常常让人觉得是世界的中心',
    '喜欢搞恶作剧的家伙，总能在你最意想不到的时候给你惊喜或惊吓。总是带着一种狡黠的笑容，让人又爱又恨',
    '社交达人，擅长与人打成一片。不论是在聚会还是在工作场合，都能迅速成为焦点，带动大家的情绪',
    '一个完美主义者，对自己和周围的一切都有很高的要求。喜欢追求细节上的极致，总是希望所有事情都能按照理想标准进行',
    "说话风格严肃，喜欢以'实际上'开头, 但总喜欢否定别人",
    '玩世不恭，总是以一种嘲讽的语气说话，让人感觉他总是对这个世界充满了不满',
    '暴躁易怒，说话总是带着火药味，动不动就威胁要打人，但其实内心很善良'
]


if __name__ == '__main__':
    host = GameHost(name='主持人', member_id='werewolf_host')
    # host.signup()
    host.login()
    # _, wolves_chat = host.create_chat('wolves_chat')
    # _, villagers_chat = host.create_chat('villagers_chat')
    # print('wolves_chat_id:', wolves_chat.chat_id)
    # print('villagers_chat_id:', villagers_chat.chat_id)

    villagers_chat_id = '2027a18b-4ec3-49c5-ad6a-5f0ab6f5f104'
    wolves_chat_id = 'b83ddd90-2363-46a2-93ab-2d135dd6234c'

    # 注册
    villager1 = Villager(name='天真无邪小可爱', member_id='villager_001', style=styles[0],
                         villager_chat_id=villagers_chat_id)
    villager2 = Villager(name='段子手张三', member_id='villager_002', style=styles[1],
                         villager_chat_id=villagers_chat_id)

    werewolf = Werewolf(name='诗魂李白', member_id='villager_003', style=styles[2], villager_chat_id=villagers_chat_id,
                        werewolf_chat_id=wolves_chat_id)

    villager3 = Villager(name='傲娇王子', member_id='villager_004', style=styles[3], villager_chat_id=villagers_chat_id)
    prophet = Prophet(name='捣蛋鬼小明', member_id='villager_005', style=styles[4], villager_chat_id=villagers_chat_id)

    villager4 = Villager(name='交际花小芳', member_id='villager_006', style=styles[5],
                         villager_chat_id=villagers_chat_id)

    witch = Witch(name='完美强迫症', member_id='villager_007', style=styles[6], villager_chat_id=villagers_chat_id)
    werewolf2 = Werewolf(name='杠精老王', member_id='villager_008', style=styles[7], villager_chat_id=villagers_chat_id,
                         werewolf_chat_id=wolves_chat_id)

    villager6 = Villager(name='愤世嫉俗哥', member_id='villager_009', style=styles[8],
                         villager_chat_id=villagers_chat_id)

    werewolf3 = Werewolf(name='暴躁狼王', member_id='villager_010', style=styles[9], villager_chat_id=villagers_chat_id,
                         werewolf_chat_id=wolves_chat_id)
    villagers = [villager1, villager2, werewolf, villager3, prophet, villager4, witch, werewolf2, villager6, werewolf3]

    for v in villagers:
        # v.signup()
        v.login()
    # host.pull_members_into_chat(villagers_chat_id, [v.member_id for v in villagers])
    # host.pull_members_into_chat(wolves_chat_id, [v.member_id for v in [werewolf, werewolf2, werewolf3]])

    # host.register_chat_manager(wolves_chat_id)
    # host.register_chat_manager(villagers_chat_id)
    host.villager_ids = [v.member_id for v in villagers]
    host.wolves_chat_id = wolves_chat_id
    host.villagers_chat_id = villagers_chat_id
    werewolf.host_member_id = host.member_id
    werewolf2.host_member_id = host.member_id
    werewolf3.host_member_id = host.member_id
    input('输入回车开始游戏')
    host.start_night_phase()
    host.socket.wait()
