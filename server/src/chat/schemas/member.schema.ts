// member.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type MemberDocument = Member & Document;
@Schema({ timestamps: true })
export class Member {
  @Prop({ required: true, unique: true, index: true })
  member_id: string;

  @Prop({ required: true, index: true })
  name: string;

  @Prop({ type: [String], default: [], index: true }) // 为 chats 字段添加索引
  chats: string[];

  @Prop({ type: String, required: false })
  avatar: string;

  @Prop({ type: String, required: false })
  description: string;

  // 监听的聊天列表
  @Prop({ type: [String], default: [], index: true })
  listen_in_chats: string[];

  // 定义复合索引
  static indexes = [
    { name: 1, chats: 1 }, // 在 name 和 chats 字段上添加复合索引
  ];
}

export const MemberSchema = SchemaFactory.createForClass(Member);
