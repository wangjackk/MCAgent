import { Injectable } from '@nestjs/common';
import { ChatRepositoryService } from './repository/chat.repo';
import { Chat } from './schemas/chat.schema';
import { Message } from './schemas/message.schema';

@Injectable()
export class ChatService {
  constructor(private chatRepository: ChatRepositoryService) {}

  async createChat(
    chat_id: string,
    name: string,
    created_by: string,
    is_group: boolean = true,
    description: string = '',
  ): Promise<{
    status: 'success' | 'failed' | 'exists';
    data?: Chat;
    message: string;
  }> {
    try {
      // 创建新聊天
      const newChat = await this.chatRepository.createChat(
        chat_id,
        name,
        created_by,
        is_group,
        description,
      );

      console.log(`New chat created: ${newChat.chat_id}`);
      return {
        status: 'success', // 返回成功状态
        data: newChat,
        message: `Chat with id ${chat_id} created successfully.`,
      };
    } catch (error) {
      console.error(`Failed to create chat: ${error.message}`);
      return {
        status: 'failed', // 返回失败状态
        message: `Failed to create chat. Error: ${error.message}`,
      };
    }
  }

  async addMember(chat_id: string, member_id: string) {
    // 如果成员在监听列表中，则移除
    const chat = await this.getChat(chat_id);
    if (chat.listeners.includes(member_id)) {
      await this.chatRepository.removeListener(chat_id, member_id);
    }
    return this.chatRepository.addMember(chat_id, member_id);
  }

  async getMembers(chat_id: string) {
    return this.chatRepository.getMembers(chat_id);
  }

  async clearMessages(chat_id: string) {
    return this.chatRepository.clearMessages(chat_id);
  }

  async clearMembers(chat_id: string) {
    return this.chatRepository.clearMembers(chat_id);
  }

  async getJoinedChats(member_id: string): Promise<string[]> {
    const chats = await this.chatRepository.getJoinedChats(member_id);
    return chats.map((chat) => chat.chat_id);
  }

  async getChat(chat_id: string): Promise<Chat> {
    return this.chatRepository.getChat(chat_id);
  }

  async deleteChat(chat_id: string): Promise<Chat> {
    return this.chatRepository.deleteChat(chat_id);
  }

  async removeMember(chat_id: string, member_id: string): Promise<Chat> {
    return this.chatRepository.exitChat(chat_id, member_id);
  }

  async addMessageToChat(chat_id: string, message_id: string) {
    return this.chatRepository.addMessageToChat(chat_id, message_id);
  }

  async getCreatedChatsByMemberId(member_id: string): Promise<Chat[]> {
    return this.chatRepository.getCreatedChatsByMemberId(member_id);
  }

  async getMessages(chat_id: string, count: number): Promise<string[]> {
    return this.chatRepository.getMessages(chat_id, count);
  }

  async setChatManager(chat_id: string, manager_id: string): Promise<Chat> {
    return this.chatRepository.setChatManager(chat_id, manager_id);
  }

  async getChatManager(chat_id: string): Promise<string | null> {
    return this.chatRepository.getChatManager(chat_id);
  }

  async addListener(
    chat_id: string,
    listener_member_id: string,
  ): Promise<Chat> {
    //检查chat_id是否存在
    const chat = await this.getChat(chat_id);
    if (!chat) {
      console.log('Chat not found');
    }
    //检查member_id是否已经在members列表中,在就禁止添加
    const members = await this.getMembers(chat_id);
    if (members.includes(listener_member_id)) {
      console.log('Member already in members list');
      return;
    }

    //检查member_id是否已经在listeners列表中,在就禁止添加
    const listeners = await this.getListeners(chat_id);
    if (listeners.includes(listener_member_id)) {
      console.log('Member already in listeners list');
      return;
    }

    return this.chatRepository.addListener(chat_id, listener_member_id);
  }

  async getListeners(chat_id: string): Promise<string[]> {
    return this.chatRepository.getListeners(chat_id);
  }

  async removeListener(
    chat_id: string,
    listener_member_id: string,
  ): Promise<Chat> {
    return this.chatRepository.removeListener(chat_id, listener_member_id);
  }
}
