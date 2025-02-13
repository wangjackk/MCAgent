import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type ChatDocument = Chat & Document;

@Schema({ timestamps: true })
export class Chat {
  @Prop({ required: true, unique: true, index: true })
  chat_id: string;

  @Prop({ type: String, required: true })
  name: string;

  @Prop({ type: [String], required: true })
  members: string[];

  @Prop({ type: [String], default: [] })
  messages: string[];

  // 是否是群聊,如果没有该字段,则默认是群聊
  @Prop({ type: Boolean, default: true })
  is_group: boolean;

  //createdBy
  @Prop({ type: String, required: true })
  created_by: string;

  //description
  @Prop({ type: String, default: '' })
  description: string;

  //manager
  @Prop({ type: String, default: '' })
  manager: string;

  //监听者
  @Prop({ type: [String], default: [] })
  listeners: string[];
}

export const ChatSchema = SchemaFactory.createForClass(Chat);
