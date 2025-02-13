import { Injectable } from '@nestjs/common';
import { Member } from './schemas/member.schema';
import { MemberRepositoryService } from './repository/member.repo';

@Injectable()
export class MemberService {
  constructor(private readonly memberRepo: MemberRepositoryService) {}

  async createMember(
    memberId: string,
    name: string,
    description?: string,
  ): Promise<boolean> {
    if (await this.memberRepo.getMember(memberId)) {
      return false;
    }
    await this.memberRepo.createMember(name, memberId, description);
    return true;
  }

  async updateMember(
    memberId: string,
    data: { name?: string; description?: string; chats?: string[] },
  ): Promise<boolean> {
    if (!(await this.memberRepo.getMember(memberId))) {
      return false;
    }
    await this.memberRepo.updateMember(memberId, data);
    return true;
  }

  async joinChat(memberId: string, chatId: string): Promise<Member | null> {
    // 获取成员信息
    const member = await this.memberRepo.getMember(memberId);
    if (!member) {
      throw new Error('Member not found');
    }

    // 获取当前的聊天列表，确保它是数组
    const currentChats: string[] = member.chats || [];

    // 如果已存在 chatId，则直接返回成员对象
    if (currentChats.includes(chatId)) {
      return member;
    }

    // 如果成员在监听列表中，则移除
    if (member.listen_in_chats.includes(chatId)) {
      await this.memberRepo.unListenInChat(memberId, chatId);
    }

    // 否则，追加新的 chatId
    const updatedChats = [...currentChats, chatId];
    return this.memberRepo.updateMember(memberId, {
      chats: updatedChats,
    });
  }

  // 获取所有成员
  async getAllMembers(): Promise<Member[]> {
    return this.memberRepo.getAllMembers();
  }

  async getChats(memberId: string) {
    return this.memberRepo.getMemberChats(memberId);
  }

  async getMember(memberId: string): Promise<Member | null> {
    return this.memberRepo.getMember(memberId);
  }

  async getMemberByName(name: string, chat_id: string): Promise<Member | null> {
    return this.memberRepo.getMemberByName(name, chat_id);
  }

  async getMembers(memberIds: string[]): Promise<Member[]> {
    return this.memberRepo.getMembers(memberIds);
  }

  async exitChat(member_id: string, chat_id: string): Promise<Member | null> {
    return this.memberRepo.exitChat(member_id, chat_id);
  }

  async listenInChat(
    member_id: string,
    chat_id: string,
  ): Promise<Member | null> {
    return this.memberRepo.listenInChat(member_id, chat_id);
  }

  async unListenInChat(
    member_id: string,
    chat_id: string,
  ): Promise<Member | null> {
    return this.memberRepo.unListenInChat(member_id, chat_id);
  }
}
