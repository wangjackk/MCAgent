import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Chat, ChatDocument } from '../schemas/chat.schema';
import { Model } from 'mongoose';

@Injectable()
export class ChatRepositoryService {
  constructor(@InjectModel(Chat.name) private chatModel: Model<ChatDocument>) {}

  // 创建新聊天
  async createChat(
    chat_id: string,
    name: string,
    created_by: string,
    is_group: boolean,
    description: string,
  ): Promise<Chat> {
    const newChat = new this.chatModel({
      chat_id,
      name,
      is_group,
      created_by,
      description,
    });

    return newChat.save();
  }

  // 添加成员
  async addMember(chat_id: string, member_id: string): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $addToSet: { members: member_id } },
        { new: true },
      )
      .exec();
  }

  // 获取聊天成员
  async getMembers(chat_id: string): Promise<string[] | null> {
    const chat = await this.chatModel.findOne({ chat_id }).exec();
    return chat ? chat.members : null;
  }

  // 清空消息
  async clearMessages(chat_id: string): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $set: { messages: [] } }, // 清空消息
        { new: true },
      )
      .exec();
  }

  // 清空成员
  async clearMembers(chat_id: string): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $set: { members: [] } }, // 清空成员
        { new: true },
      )
      .exec();
  }

  // 删除聊天
  async deleteChat(chat_id: string): Promise<Chat | null> {
    return this.chatModel.findOneAndDelete({ chat_id }).exec();
  }

  async getChat(chat_id: string): Promise<Chat | null> {
    return this.chatModel.findOne({ chat_id }).exec();
  }

  async exitChat(chat_id: string, member_id: string): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $pull: { members: member_id } },
        { new: true },
      )
      .exec();
  }

  async getChatMessageIds(
    chatId: string,
    count: number = -1,
  ): Promise<string[]> {
    const chat = await this.chatModel
      .findOne({ chat_id: chatId })
      .select('messages') // 获取消息字段
      .exec();

    if (!chat || !chat.messages) {
      return [];
    }

    // 如果 count = -1，返回所有消息
    if (count === -1) {
      return chat.messages;
    }

    // 获取倒数 count 条消息
    const messageIds = chat.messages.slice(-count);

    return messageIds;
  }

  async isGroupChat(chat_id: string): Promise<boolean> {
    const chat = await this.chatModel.findOne({ chat_id }).exec();
    // 如果 该 chat 没有 is_group 字段,则默认是群聊
    return chat?.is_group || true;
  }

  async getJoinedChats(member_id: string): Promise<Chat[]> {
    return this.chatModel.find({ members: member_id }).exec();
  }

  async addMessageToChat(chat_id: string, message_id: string) {
    return this.chatModel.findOneAndUpdate(
      { chat_id },
      { $addToSet: { messages: message_id } },
      { new: true },
    );
  }

  async getCreatedChatsByMemberId(member_id: string): Promise<Chat[]> {
    return this.chatModel.find({ created_by: member_id }).exec();
  }

  async getMessages(chat_id: string, count: number): Promise<string[]> {
    return this.getChatMessageIds(chat_id, count);
  }

  async setChatManager(
    chat_id: string,
    manager_id: string,
  ): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate({ chat_id }, { manager: manager_id }, { new: true })
      .exec();
  }

  async getChatManager(chat_id: string): Promise<string | null> {
    const chat = await this.chatModel.findOne({ chat_id }).exec();
    return chat?.manager || null;
  }

  async addListener(
    chat_id: string,
    listener_member_id: string,
  ): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $addToSet: { listeners: listener_member_id } },
        { new: true },
      )
      .exec();
  }

  async getListeners(chat_id: string): Promise<string[]> {
    const chat = await this.chatModel.findOne({ chat_id }).exec();
    return chat?.listeners || [];
  }

  async removeListener(
    chat_id: string,
    listener_member_id: string,
  ): Promise<Chat | null> {
    return this.chatModel
      .findOneAndUpdate(
        { chat_id },
        { $pull: { listeners: listener_member_id } },
        { new: true },
      )
      .exec();
  }
}
