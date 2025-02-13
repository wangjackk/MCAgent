import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Member, MemberDocument } from '../schemas/member.schema';

@Injectable()
export class MemberRepositoryService {
  constructor(
    @InjectModel(Member.name) private memberModel: Model<MemberDocument>,
  ) {}

  async createMember(
    name: string,
    member_id: string,
    description?: string,
  ): Promise<Member> {
    const newMember = new this.memberModel({
      name,
      member_id,
      description,
      chats: [], // 可以保持 chats 为空数组
    });
    return newMember.save();
  }

  // 通过 ID 查询成员
  async getMember(member_id: string): Promise<Member | null> {
    return this.memberModel.findOne({ member_id }).exec();
  }

  async getMemberByName(name: string, chat_id: string): Promise<Member | null> {
    return this.memberModel
      .findOne({
        name,
        chats: { $elemMatch: { $eq: chat_id } }, // chats 中包含 chat_id
      })
      .exec();
  }

  async getMembers(memberIds: string[]): Promise<Member[]> {
    return this.memberModel.find({ member_id: { $in: memberIds } }).exec();
  }

  // 通过 ID 更新成员的 name 和 description
  async updateMember(
    member_id: string,
    data: { name?: string; description?: string; chats?: string[] },
  ): Promise<Member | null> {
    const updateData: any = {};

    // 仅更新传入的数据字段
    if (data.name !== undefined) {
      updateData['name'] = data.name;
    }
    if (data.description !== undefined) {
      updateData['description'] = data.description;
    }
    if (data.chats !== undefined) {
      updateData['$addToSet'] = { chats: { $each: data.chats } }; // 避免重复并添加新值
    }

    return this.memberModel
      .findOneAndUpdate(
        { member_id },
        updateData,
        { new: true }, // 返回更新后的文档
      )
      .exec();
  }

  async getAllMembers(): Promise<Member[]> {
    return this.memberModel
      .find({}, { name: 1, member_id: 1, description: 1 })
      .exec();
  }

  async getMemberChats(member_id: string): Promise<string[] | null> {
    const member = await this.memberModel
      .findOne({ member_id }, { chats: 1 })
      .exec();
    return member ? member.chats : null;
  }

  async exitChat(member_id: string, chatId: string): Promise<Member | null> {
    // 获取更新前的成员数据
    // console.log(`开始获取${member_id}的成员数据`);
    // const beforeMember = await this.getMember(member_id);
    // console.log(`获取${member_id}的成员数据成功:${beforeMember}`);
    // console.log(`退出聊天前的 ${member_id} chats:`, beforeMember?.chats);

    const updatedMember = await this.memberModel
      .findOneAndUpdate(
        { member_id },
        {
          $pull: { chats: chatId },
        },
        { new: true },
      )
      .exec();

    // console.log(`退出聊天后的 ${member_id} chats:`, updatedMember?.chats);
    return updatedMember;
  }

  async listenInChat(
    member_id: string,
    chatId: string,
  ): Promise<Member | null> {
    // chatid 是否在chats列表中
    return this.memberModel
      .findOneAndUpdate(
        { member_id },
        { $addToSet: { listen_in_chats: chatId } },
        { new: true },
      )
      .exec();
  }

  async getListenInChats(member_id: string): Promise<string[]> {
    const member = await this.memberModel
      .findOne({ member_id }, { listen_in_chats: 1 })
      .exec();
    return member ? member.listen_in_chats : [];
  }

  async unListenInChat(
    member_id: string,
    chatId: string,
  ): Promise<Member | null> {
    return this.memberModel
      .findOneAndUpdate(
        { member_id },
        { $pull: { listen_in_chats: chatId } },
        { new: true },
      )
      .exec();
  }
}
