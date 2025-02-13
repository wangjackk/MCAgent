import {
  OnGatewayConnection,
  OnGatewayDisconnect,
  SubscribeMessage,
  WebSocketGateway,
  WebSocketServer,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Injectable, Logger } from '@nestjs/common';
import { EventsClient, EventsServer } from './chat.events';
import { v4 as uuidv4 } from 'uuid';

import { OnlineMembersService } from './online_members.service';
import { ChatService } from './chat.service';
import { MemberService } from './member.service';
import { MessageService } from './message.service';
import { CommandDto } from './dto/command.dto';

@WebSocketGateway({ cors: true })
@Injectable()
export class ChatGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer() server: Server;
  private readonly logger = new Logger(ChatGateway.name);

  constructor(
    private readonly onlineMembersService: OnlineMembersService,
    private readonly memberService: MemberService,
    private readonly chatService: ChatService,
    private readonly messageService: MessageService,
  ) {}

  // 当客户端连接时触发
  async handleConnection(client: Socket): Promise<void> {
    const { member_id, member_name } = client.handshake.auth;
    // 如果没有提供 member_id 和 member_name，则拒绝连接
    if (!member_id || !member_name) {
      client.emit(EventsClient.RECEIVE_LOGIN_RESPONSE, {
        status: 400,
        message: 'Missing member_id or member_name',
      });
      client.disconnect();
      return;
    }

    try {
      // 验证成员是否存在
      const member = await this.memberService.getMember(member_id);

      // 如果成员不存在，拒绝连接
      if (!member) {
        client.emit(EventsClient.RECEIVE_LOGIN_RESPONSE, {
          status: 404,
          message: `MemberId ${member_id} does not exist`,
        });
        client.disconnect();
        return;
      }

      // 如果提供了认证信息并且成员存在，处理登录逻辑
      await this.onlineMembersService.updateOnlineMember(member_id, client);
      await this.memberService.updateMember(member_id, { name: member_name });

      console.log('members:', JSON.stringify(member));

      // 发送登录成功消息
      client.emit(EventsClient.RECEIVE_LOGIN_RESPONSE, {
        status: 200,
        message: `${member_name} ${member_id} login success`,
        data: { member_id, member_name },
      });

      this.logger.log(`${member_name} (${member_id}) connected successfully.`);
    } catch (error) {
      this.logger.error(
        `Login error for member ${member_name}: ${error.message}`,
      );
      client.emit(EventsClient.RECEIVE_LOGIN_RESPONSE, {
        status: 500,
        message: 'Login failed due to server error',
      });
      client.disconnect();
    }
  }

  // 断开连接时触发
  async handleDisconnect(client: Socket): Promise<void> {
    await this.onlineMembersService.removeOnlineMemberBySocket(client);
  }

  @SubscribeMessage(EventsServer.SEND_MESSAGE)
  async handleMessage(client: Socket, data: any): Promise<any> {
    const chat_id = data.chat_id;
    console.log('send message:', data);

    //检测member_id是否存在
    const member = await this.memberService.getMember(data.from_member_id);
    if (!member) {
      return {
        message_id: data.message_id,
        status: 'failed',
        message: 'Member not found',
      };
    }

    //检测chatid是否存在
    const chat = await this.chatService.getChat(chat_id);
    if (!chat) {
      return {
        message_id: data.message_id,
        status: 'failed',
        message: 'Chat not found',
      };
    }

    //检测发送者是否在聊天中
    const members = await this.chatService.getMembers(chat_id);
    if (!members.includes(data.from_member_id)) {
      return {
        message_id: data.message_id,
        status: 'failed',
        message: 'Sender not in chat',
      };
    }

    // 排除发送者
    const membersWithoutSender = members.filter(
      (member: string) => member !== data.from_member_id,
    );

    // 获取监听者
    const listeners = await this.chatService.getListeners(chat_id);

    //获取在线成员
    const onlineMembers = await this.onlineMembersService.getOnlineMembers();

    //合并membersWithoutSender和listeners, 避免重复
    // const membersToSend_ = [...membersWithoutSender, ...listeners];

    const membersToSendSet = new Set([...membersWithoutSender, ...listeners]);

    //只发给在线成员
    const membersToSend = onlineMembers.filter((member: string) =>
      membersToSendSet.has(member),
    );

    // 发送消息并等待每个成员的确认
    const acknowledgmentPromises = membersToSend.map(async (member: string) => {
      try {
        const clientTo =
          await this.onlineMembersService.getSocketByMemberId(member);
        if (clientTo?.connected) {
          // 使用 emitWithAck 发送消息并等待确认
          const acknowledgment = await clientTo.emitWithAck(
            EventsClient.RECEIVE_MESSAGE,
            data,
          );

          // 处理确认
          if (acknowledgment == true) {
            console.log(`Message successfully delivered to ${member}`);
            return null; // 成功，返回null表示该成员已确认接收
          }
        } else {
          console.warn(`Client for member ${member} is not connected.`);
          return member; // 如果该成员未连接，返回其 ID
        }
      } catch (error) {
        console.error(`Failed to send message to member ${member}:`, error);
        return member; // 如果发生错误，返回该成员 ID
      }
    });

    // 等待所有成员的确认，或者找出未确认的成员
    const notReceivedMembers = (
      await Promise.all(acknowledgmentPromises)
    ).filter(Boolean);

    if (notReceivedMembers.length > 0) {
      console.log(
        'Message forwarding completed, not received:',
        notReceivedMembers,
      );
    } else {
      console.log('消息转发完成 √√√');
    }
    // 将消息添加到聊天记录中
    await this.messageService.addMessage(data);
    await this.chatService.addMessageToChat(chat_id, data.message_id);

    // 返回结果给发送方
    return {
      message_id: data.message_id,
      status: notReceivedMembers.length === 0 ? 'success' : 'pending',
      notReceivedMembers,
    };
  }

  @SubscribeMessage(EventsServer.CREATE_CHAT)
  async handleCreateChat(client: Socket, data: any): Promise<any> {
    console.log('create chat:', data);
    const chat_id = uuidv4();
    const created_by = client.handshake.auth.member_id;
    // 调用服务层创建聊天
    const response = await this.chatService.createChat(
      chat_id,
      data.name,
      created_by,
      data.is_group,
      data.description,
    );

    // 根据返回的状态构造响应
    if (response.status === 'success') {
      console.log(`Chat ${response.data.chat_id} created successfully.`);
      return {
        status: 'success',
        message: response.message,
        data: response.data, // 包含新创建的聊天对象
      };
    } else {
      console.error(`Failed to create chat: ${response.message}`);
      return {
        status: 'failed',
        message: response.message,
      };
    }
  }

  @SubscribeMessage(EventsServer.JOIN_CHAT)
  async handleJoinChat(client: Socket, data: any): Promise<any> {
    console.log('join chat:', data);

    // 检测chat是否存在
    const chat = await this.chatService.getChat(data.chat_id);
    if (!chat) {
      return {
        status: 'failed',
        message: 'Chat not found',
      };
    }

    // 添加成员
    await this.chatService.addMember(
      data.chat_id,
      client.handshake.auth.member_id,
    );
    const member = await this.memberService.joinChat(
      client.handshake.auth.member_id,
      data.chat_id,
    );

    // 返回结果给客户端
    return {
      chat: chat.chat_id,
      members: chat.members,
      status: chat.chat_id && member.member_id ? 'success' : 'failed',
    };
  }

  @SubscribeMessage(EventsServer.GET_ONLINE_MEMBERS)
  async handleGetOnlineMembers(): Promise<any> {
    console.log('get online members');
    return this.onlineMembersService.getOnlineMembers();
  }

  @SubscribeMessage(EventsServer.GET_CHAT_ONLINE_MEMBERS)
  async handleGetChatOnlineMembers(client: Socket, data: any): Promise<any> {
    try {
      console.log('get chat online members:', data);

      // 获取聊天成员列表
      const chat_members = await this.chatService.getMembers(data.chat_id);
      // 获取在线成员列表
      const online_members = await this.onlineMembersService.getOnlineMembers();

      // 确保 online_members 是 string[]
      const online_member_ids = online_members.map((member: any) =>
        member.toString(),
      ); // 转换为字符串数组

      // 过滤出在线且属于聊天成员的成员
      return online_member_ids.filter((member_id: string) =>
        chat_members.includes(member_id),
      );
    } catch (error) {
      console.error('Error fetching chat online members:', error);
      return [];
    }
  }

  @SubscribeMessage(EventsServer.GET_JOINED_CHATS)
  async handleGetJoinedChats(client: Socket): Promise<any> {
    console.log('get joined chats');

    return this.chatService.getJoinedChats(client.handshake.auth.member_id);
  }

  @SubscribeMessage(EventsServer.GET_CHAT)
  async handleGetChat(client: Socket, data: any): Promise<any> {
    console.log('get chat:', data);
    const chat = await this.chatService.getChat(data.chat_id);
    if (!chat) {
      return {
        status: 'failed',
        message: 'Chat not found',
      };
    }
    return {
      status: 'success',
      message: 'Chat fetched successfully',
      data: chat,
    };
  }

  @SubscribeMessage(EventsServer.DELETE_CHAT)
  async handleDeleteChat(client: Socket, data: any): Promise<any> {
    console.log('delete chat:', data);
    //检测chat是否存在
    const chat = await this.chatService.getChat(data.chat_id);
    if (!chat) {
      return {
        status: 'failed',
        message: 'Chat not found',
      };
    }
    const members = await this.chatService.getMembers(data.chat_id);
    // console.log(`exit chat members:`, members);
    for (const member of members) {
      await this.memberService.exitChat(member, data.chat_id);
    }
    await this.chatService.deleteChat(data.chat_id);

    return {
      status: 'success',
      message: 'Chat deleted successfully',
    };
  }

  @SubscribeMessage(EventsServer.EXIT_CHAT)
  async handleExitChat(client: Socket, data: any): Promise<any> {
    // console.log(
    //   `exit chat:${data.chat_id}, member:${client.handshake.auth.member_id}`,
    // );

    // 检测chat是否存在
    const chat = await this.chatService.getChat(data.chat_id);
    if (!chat) {
      return {
        status: 'failed',
        message: 'Chat not found',
      };
    }

    // 检测member是否存在
    const member = await this.memberService.getMember(
      client.handshake.auth.member_id,
    );
    if (!member) {
      return {
        status: 'failed',
        message: 'Member not found',
      };
    }

    // 检测member是否在chat中
    if (!chat.members.includes(client.handshake.auth.member_id)) {
      return {
        status: 'failed',
        message: 'Member not in chat',
      };
    }

    await this.memberService.exitChat(
      data.chat_id,
      client.handshake.auth.member_id,
    );

    await this.chatService.removeMember(
      data.chat_id,
      client.handshake.auth.member_id,
    );

    return {
      status: 'success',
      message: 'Member exited chat successfully',
    };
  }

  @SubscribeMessage(EventsServer.SEND_COMMAND)
  async handleSendCommand(client: Socket, data: CommandDto) {
    const { to, ...dataWithoutTo } = data;
    console.log('send command:', data);
    // 检测to
    if (!to || to.length === 0) {
      return {
        status: 'failed',
        message: 'To is empty',
      };
    }
    // 使用 map 收集所有的 Promise
    const promises = to.map(async (member: string) => {
      const clientTo =
        await this.onlineMembersService.getSocketByMemberId(member);
      if (clientTo?.connected) {
        try {
          const result = await clientTo.emitWithAck(
            EventsClient.RECEIVE_COMMAND,
            dataWithoutTo,
          );
          console.log(`receive ${member} command res:`, result);
          return {
            result: result,
            command: { command: data.command, by: data.by, to: member },
          };
        } catch (error) {
          console.error(`Error sending to member ${member}:`, error);
          return { member, error };
        }
      } else {
        console.warn(`Client for member ${member} is not connected.`);
        return { member, error: 'Client not connected' };
      }
    });

    // 并行执行所有的请求
    return Promise.all(promises);
  }

  @SubscribeMessage(EventsServer.PULL_MEMBERS_INTO_CHAT)
  async handlePullMembersIntoChat(client: Socket, data: any): Promise<any> {
    console.log('pull members into chat:', data);
    const chat_id = data.chat_id;
    //检测chat是否存在
    const chat = await this.chatService.getChat(chat_id);
    if (!chat) {
      return {
        status: 'failed',
        message: 'Chat not found',
      };
    }

    const newMembers = data.members;
    console.log(`new members:`, newMembers);
    //检测member是否存在
    for (const newMember of newMembers) {
      const member = await this.memberService.getMember(newMember);
      if (!member) {
        return {
          status: 'failed',
          message: `Member ${newMember} not found`,
        };
      }
      await this.memberService.joinChat(newMember, chat_id);
      await this.chatService.addMember(chat_id, newMember);
    }

    return {
      status: 'success',
      message: 'Members pulled into chat successfully',
    };
  }

  @SubscribeMessage(EventsServer.GET_MEMBER)
  async handleGetMember(client: Socket, data: any): Promise<any> {
    console.log('get member:', data);
    return this.memberService.getMember(data.member_id);
  }

  @SubscribeMessage(EventsServer.GET_MEMBERS)
  async handleGetMembers(client: Socket, data: any): Promise<any> {
    console.log('get members:', data);
    return this.memberService.getMembers(data.members);
  }

  @SubscribeMessage(EventsServer.GET_CREATED_CHATS)
  async handleGetCreatedChats(client: Socket, data: any): Promise<any> {
    console.log('get created chats:', data);
    return this.chatService.getCreatedChatsByMemberId(
      client.handshake.auth.member_id,
    );
  }

  @SubscribeMessage(EventsServer.GET_CHAT_MEMBERS)
  async handleGetChatMembers(client: Socket, data: any): Promise<any> {
    console.log('get chat members:', data);
    const member_ids = await this.chatService.getMembers(data.chat_id);
    if (!data.complete) {
      return member_ids;
    } else {
      return this.memberService.getMembers(member_ids);
    }
  }

  @SubscribeMessage(EventsServer.GET_MEMBER_BY_NAME)
  async handleGetMemberByName(client: Socket, data: any): Promise<any> {
    console.log('get member by name:', data);
    const name = data.name;
    const chat_id = data.chat_id;
    return this.memberService.getMemberByName(name, chat_id);
  }

  @SubscribeMessage(EventsServer.REMOVE_MEMBER_FROM_CHAT)
  async handleRemoveMemberFromChat(client: Socket, data: any): Promise<any> {
    console.log('remove member from chat:', data);
    const member_id = data.member_id;
    const chat_id = data.chat_id;
    await this.memberService.exitChat(member_id, chat_id);
    await this.chatService.removeMember(chat_id, member_id);
    return {
      status: 'success',
      message: 'Member removed from chat successfully',
    };
  }

  @SubscribeMessage(EventsServer.NEXT_SPEAKER)
  async handleNextSpeaker(client: Socket, data: any) {
    const clientTo = await this.onlineMembersService.getSocketByMemberId(
      data.member_id,
    );
    if (!clientTo.connected) {
      console.log('连接已断开，无法发送消息');
    }
    console.log('next speaker:', data.member_id);
    clientTo.emit(EventsClient.NEXT_SPEAKER, { chat_id: data.chat_id });
  }

  @SubscribeMessage(EventsServer.LOAD_CHAT_MESSAGES_FROM_SERVER)
  async handleLoadChatMessagesFromServer(client: Socket, data: any) {
    console.log('load chat messages from server:', data);
    const chat_id = data.chat_id;
    const count = data.count;
    const messageIds = await this.chatService.getMessages(chat_id, count);
    return this.messageService.getMessages(messageIds);
  }

  @SubscribeMessage(EventsServer.SEND_NOTIFICATION_TO_CHAT)
  async handleSendNotificationToChat(client: Socket, data: any) {
    console.log('send notification to chat:', data);
    const to_chat_id = data.to_chat_id;
    const manager_id = await this.chatService.getChatManager(to_chat_id);
    if (!manager_id) {
      return {
        status: 'failed',
        message: `Chat manager in chat id ${to_chat_id} is not found, please register chat manager first`,
      };
    }
    const manager_client =
      await this.onlineMembersService.getSocketByMemberId(manager_id);
    if (!manager_client.connected) {
      return {
        status: 'failed',
        message: 'Chat manager not connected',
      };
    }
    return manager_client.emit(
      EventsClient.RECEIVE_NOTIFICATION_FROM_CHAT,
      data,
    );
  }

  @SubscribeMessage(EventsServer.REGISTER_CHAT_MANAGER)
  async handleRegisterChatManager(client: Socket, data: any) {
    console.log('register chat manager:', data);
    const chat_id = data.chat_id;
    const manager_id = client.handshake.auth.member_id;
    await this.chatService.setChatManager(chat_id, manager_id);
    return {
      status: 'success',
      message: `Chat manager: ${manager_id} registered successfully`,
    };
  }

  @SubscribeMessage(EventsServer.LISTEN_IN_CHAT)
  async handleListenInChat(client: Socket, data: any) {
    console.log('listen in chat:', data);
    const chat_id = data.chat_id;
    const listener_member_id = client.handshake.auth.member_id;

    //检测member是否存在
    const member = await this.memberService.getMember(listener_member_id);
    if (!member) {
      return {
        status: 'failed',
        message: `Member ${listener_member_id} not found`,
      };
    }
    await this.chatService.addListener(chat_id, listener_member_id);
    await this.memberService.listenInChat(listener_member_id, chat_id);
    return {
      status: 'success',
      message: `Listener: ${listener_member_id} listened in chat: ${chat_id} successfully`,
    };
  }

  @SubscribeMessage(EventsServer.UNLISTEN_IN_CHAT)
  async handleUnlistenInChat(client: Socket, data: any) {
    console.log('unlisten in chat:', data);
    const chat_id = data.chat_id;
    const listener_member_id = client.handshake.auth.member_id;
    await this.chatService.removeListener(chat_id, listener_member_id);
    await this.memberService.unListenInChat(listener_member_id, chat_id);
    console.log('unlisten chat success', data.chat_id);
    return {
      status: 'success',
      message: `Listener: ${listener_member_id} unlistened in chat: ${chat_id} successfully`,
    };
  }
}
